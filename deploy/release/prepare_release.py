"""Build a deterministic release from a clean exact Git commit, on Windows only.

Run with the checkout's Python environment (Django/packaging already available).
No source checkout files are edited, no server is contacted, no secret is saved.
"""
import argparse
from email.parser import BytesParser
import gzip
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

DEFAULT_COMMIT = None
PINS = {"Django": "5.2.18", "asgiref": "3.12.1", "sqlparse": "0.6.0", "tzdata": "2026.5", "whitenoise": "6.12.0", "gunicorn": "26.2.0", "Pillow": "13.0.0", "PyJWT": "2.15.1", "cryptography": "50.0.2", "cffi": "2.1.1", "pycparser": "3.12"}
HOSTS = ["app.dispensalud.site", "www.dispensalud.site", "dispensalud.site"]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--commit", default=DEFAULT_COMMIT)
parser.add_argument("--repo", type=Path, required=True)
parser.add_argument("--output-dir", type=Path, required=True)
parser.add_argument("--recipe-dir", type=Path, default=Path(__file__).resolve().parent)
args = parser.parse_args()
repo, output, recipe = args.repo.resolve(), args.output_dir.resolve(), args.recipe_dir.resolve()
COMMIT = args.commit or subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
assert sys.platform == "win32", "Frontend build must run on Windows for this recipe"
assert not output.is_relative_to(repo), "Output must be outside Git checkout"
def git(*arguments):
    return subprocess.check_output(["git", "-C", str(repo), *arguments])
assert git("rev-parse", "HEAD").decode().strip() == COMMIT, "Wrong source commit"
assert not git("status", "--porcelain"), "Preserve pending work; use a clean reviewed source checkout"
subprocess.run(["npm.cmd", "run", "build"], cwd=repo / "web", check=True)
assert not git("status", "--porcelain"), "Build output differs from exact reviewed commit"
output.mkdir(parents=True, exist_ok=True)
release = output / ("dispensalud-web-" + COMMIT)
release.mkdir()  # refuse to overwrite earlier work
epoch = int(git("show", "-s", "--format=%ct", COMMIT).decode().strip())
source_files = {}
def digest(data):
    return hashlib.sha256(data).hexdigest()
def write(path, content):
    target = release / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        target.write_bytes(content)
    else:
        target.write_text(content, encoding="utf-8", newline="\n")
def allowed_source(name):
    path = Path(name)
    if name == "web/manage.py":
        return True
    if name.startswith("web/config/") and path.suffix == ".py":
        return path.name != "legacy_urls.py"
    if name.startswith("web/portal/") and path.suffix == ".py":
        return not path.name.startswith("test") and not any(part in {"tests", "__pycache__", "migrations"} for part in path.parts)
    if name.startswith("web/portal/templates/"):
        return path.suffix == ".html"
    if name.startswith("web/portal/static/"):
        return path.suffix.lower() in {".js", ".css", ".png", ".jpg", ".webp", ".svg", ".woff2", ".txt"}
    return False
with tarfile.open(fileobj=BytesIO(git("-c", "core.autocrlf=false", "archive", "--format=tar", COMMIT, "web")), mode="r:") as archive:
    for member in archive:
        if not member.isfile() or not allowed_source(member.name):
            continue
        data = archive.extractfile(member).read()
        write(member.name, data)
        source_files[member.name] = digest(data)
for asset in ("portal/static/portal/firebase/app.js", "portal/static/portal/firebase/panel-web.css"):
    actual = (repo / "web" / asset).read_bytes().replace(b"\r\n", b"\n")
    assert actual == (release / "web" / asset).read_bytes(), "Compiled resource is not from source commit"
shutil.copytree(recipe / "inputs", release, dirs_exist_ok=True)
write("docs/FOTOS_PRIVADAS_CONTRATO.md", git("show", COMMIT + ":docs/FOTOS_PRIVADAS_CONTRATO.md"))
for template in release.rglob("*"):
    if template.is_file() and template.suffix in {".md", ".example", ".py", ".sh", ".in"}:
        text = template.read_text(encoding="utf-8").replace("@WEB_COMMIT@", COMMIT)
        template.write_text(text, encoding="utf-8", newline="\n")
write("reproduce/prepare_release.py", Path(__file__).read_text(encoding="utf-8").replace("DEFAULT_COMMIT = None", "DEFAULT_COMMIT = " + repr(COMMIT)))
shutil.copytree(recipe / "inputs", release / "reproduce/inputs")
metadata = json.loads((recipe / "pypi-metadata.json").read_text(encoding="utf-8"))
selected = [entry for entry in metadata if entry["name"] in PINS]
assert len(selected) == len(PINS)
write("reproduce/pypi-metadata.json", json.dumps(selected, indent=2, ensure_ascii=False) + "\n")
environment = {**default_environment(), "python_version": "3.14", "python_full_version": "3.14.4", "sys_platform": "linux", "os_name": "posix", "platform_system": "Linux", "implementation_name": "cpython", "extra": ""}
versions = {name.lower(): Version(version) for name, version in PINS.items()}
rows, requirement_lines = [], ["# Offline production wheels. No extras or test tools.\n"]
for entry in selected:
    name, version = entry["name"], entry["version"]
    assert version == PINS[name]
    assert Version("3.14.4") in SpecifierSet(entry["requires_python"])
    assert not entry.get("vulnerabilities"), (name, "PyPI advisory: review before packaging")
    hashes = []
    for wheel in entry["wheels"]:
        target = release / "wheelhouse" / wheel["filename"]
        target.parent.mkdir(exist_ok=True)
        with urllib.request.urlopen(wheel["url"], timeout=60) as response:
            data = response.read()
        assert digest(data) == wheel["digests"]["sha256"]
        target.write_bytes(data)
        with zipfile.ZipFile(target) as zipped:
            info = BytesParser().parsebytes(zipped.read(next(path for path in zipped.namelist() if path.endswith(".dist-info/METADATA"))))
            assert info["Version"] == version and Version("3.14.4") in SpecifierSet(info["Requires-Python"])
            for dependency in info.get_all("Requires-Dist", []):
                requirement = Requirement(dependency)
                if requirement.marker is None or requirement.marker.evaluate(environment):
                    assert requirement.name.lower() in versions, (name, dependency)
                    assert versions[requirement.name.lower()] in requirement.specifier
        hashes.append("--hash=sha256:" + digest(data))
        rows.append({"name":name,"version":version,"requires_python":entry["requires_python"],"explicit_3_14_classifier":any(c.endswith("Python :: 3.14") for c in entry["classifiers"]),"wheel":wheel["filename"],"sha256":digest(data),"source":entry["source"]})
    requirement_lines.append(f"{name}=={version} " + " ".join(hashes) + "\n")
write("requirements-production.txt", "".join(requirement_lines))
write("DEPENDENCY_AUDIT.json", json.dumps({"target": "CPython 3.14.4 / Linux", "dependency_closure_verified": True, "packages": rows, "limits": ["Metadata review only; no Ubuntu runtime execution", "Gunicorn 26.2.0 allows >=3.10 but classifiers and published CI stop at 3.13", "tzdata is interpreter-neutral zone data with Requires-Python >=2"]}, indent=2) + "\n")

# Collect/compress static files on Windows without writing any production key.
validation_state = output / "windows-validation-state"
validation_state.mkdir()
env = {**os.environ, "DJANGO_DEBUG": "0", "DJANGO_SECRET_KEY": __import__("secrets").token_urlsafe(64), "DJANGO_ALLOWED_HOSTS": ",".join(HOSTS), "DJANGO_CSRF_TRUSTED_ORIGINS": ",".join("https://" + host for host in HOSTS), "DJANGO_BEHIND_PROXY": "1", "DJANGO_DATA_DIR": str(validation_state), "DISPENSALUD_HOSTED_DEMO": "0", "DISPENSALUD_FIREBASE_EMULATORS": "0", "DISPENSALUD_REGISTRATION_ENABLED": "0", "PYTHONDONTWRITEBYTECODE": "1"}
python = repo / "web/.venv/Scripts/python.exe"
for command in (["manage.py", "collectstatic", "--noinput"], ["manage.py", "check", "--deploy", "--fail-level", "ERROR"]):
    subprocess.run([str(python), *command], cwd=release / "web", env=env, check=True)
validation_script = r'''
from io import BytesIO
import json, os, sys
from pathlib import Path
os.environ['DJANGO_SETTINGS_MODULE']='config.settings'
from django.core.wsgi import get_wsgi_application
from django.conf import settings
application=get_wsgi_application()
def request(path, host='app.dispensalud.site', forwarded='https', encoding='identity'):
    captured={}
    def start(status,headers,exc_info=None): captured.update(status=int(status.split()[0]),headers=dict(headers))
    environ={'REQUEST_METHOD':'GET','PATH_INFO':path,'QUERY_STRING':'','SERVER_NAME':host,'SERVER_PORT':'8002','SERVER_PROTOCOL':'HTTP/1.1','HTTP_HOST':host,'wsgi.url_scheme':'http','wsgi.version':(1,0),'wsgi.input':BytesIO(b''),'wsgi.errors':sys.stderr,'wsgi.multithread':False,'wsgi.multiprocess':False,'wsgi.run_once':False,'HTTP_ACCEPT_ENCODING':encoding}
    if forwarded: environ['HTTP_X_FORWARDED_PROTO']=forwarded
    result=application(environ,start)
    try: captured['body']=b''.join(result)
    finally:
        if hasattr(result,'close'):result.close()
    return captured
routes=['/','/ingresar/','/cuenta/crear/','/cuenta/recuperar/','/cuenta/verificar/','/panel/','/pacientes/','/tratamientos/','/historial/','/alertas/','/equipo/','/perfil/','/salud/']
for path in routes:
    response=request(path)
    assert response['status']==200,(path,response['status'])
    assert 'includeSubDomains' not in response['headers'].get('Strict-Transport-Security','')
    if path not in ['/','/salud/']:
        assert b'"emulators": false' in response['body']
        assert '9098' not in response['headers']['Content-Security-Policy']
assert request('/api/photos/v1/')['status']==401
assert request('/api/photos/v1/profile/')['status']==401
for host in settings.ALLOWED_HOSTS: assert request('/ingresar/',host)['status']==200
assert request('/ingresar/','invalid.example')['status']==400
assert request('/ingresar/',forwarded=None)['status']==301
static_files=[path for path in settings.STATIC_ROOT.rglob('*') if path.is_file() and not path.name.endswith(('.gz','.br'))]
for path in static_files: assert request('/static/'+path.relative_to(settings.STATIC_ROOT).as_posix())['status']==200
compressed=request('/static/portal/firebase/app.js',encoding='gzip')
assert compressed['status']==200 and compressed['headers'].get('Content-Encoding')=='gzip'
assert settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE and settings.SESSION_COOKIE_HTTPONLY
print(json.dumps({'platform':sys.platform,'python':sys.version.split()[0],'real_ubuntu_execution':False,'routes_ok':len(routes),'static_files_ok':len(static_files),'hosts_ok':settings.ALLOWED_HOSTS,'reject_unknown_host':True,'https_proxy_no_redirect_loop':True,'http_redirect':True,'gzip_bundle_ok':True,'secure_cookie_settings':True,'firebase_emulators':settings.FIREBASE_EMULATORS,'photo_api_requires_bearer':True}))
'''
result = subprocess.run([str(python), "-c", validation_script], cwd=release / "web", env=env, check=True, capture_output=True, text=True)
validation = json.loads(result.stdout.strip().splitlines()[-1])
local_versions = json.loads(subprocess.check_output([str(python), "-c", "import importlib.metadata,json; print(json.dumps({name:importlib.metadata.version(name) for name in ['Django','asgiref','sqlparse','tzdata','whitenoise','Pillow','PyJWT','cryptography','cffi','pycparser']}))"], text=True))
assert all(local_versions[name] == PINS[name] for name in local_versions), "Local validation dependencies differ from release pins"
(output / "WINDOWS_VALIDATION.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
write("WINDOWS_VALIDATION.json", json.dumps(validation, indent=2) + "\n")
sizes = {"source_bytes": sum((release / path).stat().st_size for path in source_files), "staticfiles_bytes": sum(path.stat().st_size for path in (release / "web/staticfiles").rglob("*") if path.is_file()), "wheel_bytes": sum(path.stat().st_size for path in (release / "wheelhouse").glob("*.whl"))}
write("RELEASE.json", json.dumps({"git_commit": COMMIT, "git_branch": "feature/firebase-web", "git_commit_epoch": epoch, "source_files_sha256": source_files, "frontend_built_on": "Windows", "native_wheel_targets": ["CPython 3.14 Linux x86_64", "CPython 3.14 Linux aarch64"], "build_tools": {"python": validation["python"], "node": subprocess.check_output(["node", "--version"], text=True).strip(), "npm": subprocess.check_output(["npm.cmd", "--version"], text=True).strip(), "esbuild": "0.28.2", "postcss": "8.5.33", "firebase": "13.3.0"}, "production_dependencies": PINS, "hosts": HOSTS, "canonical_url": "https://www.dispensalud.site", "validation_url": "https://app.dispensalud.site", "bind": "127.0.0.1:8002", "workers": 1, "memory_high_mib": 128, "memory_max_mib": 192, "target_ubuntu": "26.04 LTS", "target_python": "3.14.4", "sizes": sizes, "real_ubuntu_execution": False, "deployed": False}, indent=2) + "\n")
for path in release.rglob("*"):
    if not path.is_file():
        continue
    relative = path.relative_to(release)
    assert not any(part in {".git", ".venv", "node_modules", "__pycache__", "data", "tests", "testdata"} for part in relative.parts), relative
    assert path.suffix not in {".log", ".db", ".sqlite", ".pem", ".key"}, relative
    assert not path.name.startswith(".env"), relative
    if path.suffix not in {".whl", ".png", ".jpg", ".webp", ".woff2", ".gz"}:
        assert not re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\b(?:AKIA|ASIA)[A-Z0-9]{16}\b|\bghp_[A-Za-z0-9]{30,}\b', path.read_bytes()), relative
checksums = [digest(path.read_bytes()) + "  " + path.relative_to(release).as_posix() for path in sorted(release.rglob("*")) if path.is_file()]
write("SHA256SUMS", "\n".join(checksums) + "\n")

def tar_bytes():
    buffer = BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", filename="", mtime=0, compresslevel=9) as zipped:
        with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for path in sorted(release.rglob("*")):
                if not path.is_file():
                    continue
                info = tarfile.TarInfo(release.name + "/" + path.relative_to(release).as_posix())
                info.size = path.stat().st_size
                info.mtime = epoch
                info.uid = info.gid = 0
                info.uname = info.gname = "root"
                info.mode = 0o755 if path.suffix == ".sh" else 0o644
                archive.addfile(info, BytesIO(path.read_bytes()))
    return buffer.getvalue()
first, second = tar_bytes(), tar_bytes()
assert first == second, "Archive output is not deterministic"
target = output / (release.name + ".tar.gz")
with target.open("xb") as archive:
    archive.write(first)
(output / (target.name + ".sha256")).write_text(digest(first) + "  " + target.name + "\n", encoding="ascii")
assert not git("status", "--porcelain"), "Checkout changed during preparation"
print(json.dumps({"archive": str(target), "sha256": digest(first), "archive_bytes": len(first), "files": len(checksums) + 1, "payload_bytes": sum(path.stat().st_size for path in release.rglob('*') if path.is_file()), "windows_validation": validation, "repeated_archive_identical": True}, indent=2))
