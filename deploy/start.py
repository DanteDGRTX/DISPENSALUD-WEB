import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import parse_qs, urlsplit


def validate_jdbc_url(value, certificate):
    if not value.startswith("jdbc:postgresql://"):
        raise RuntimeError("La conexión JDBC debe usar PostgreSQL.")
    parsed = urlsplit(value.removeprefix("jdbc:"))
    parameters = parse_qs(parsed.query)
    if parsed.username or parsed.password or "password" in parameters or "user" in parameters:
        raise RuntimeError("Configura usuario y contraseña fuera de la URL JDBC.")
    if not parsed.hostname or parameters.get("sslmode") != ["verify-full"] or parameters.get("sslrootcert") != [str(certificate)]:
        raise RuntimeError("La conexión JDBC debe verificar TLS, servidor y el mismo certificado configurado.")


def terminate(processes):
    for process in processes:
        if process.poll() is None:
            process.terminate()
    deadline = time.monotonic() + 20
    for process in processes:
        try:
            process.wait(timeout=max(0.1, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main():
    required = (
        "DJANGO_SECRET_KEY", "RENDER_EXTERNAL_HOSTNAME", "DEMO_GATE_USER", "DEMO_GATE_PASSWORD",
        "DATABASE_JDBC_URL", "DATABASE_USER", "DATABASE_PASSWORD", "DATABASE_SSL_ROOT_CERT",
        "PORTAL_DATABASE_HOST", "PORTAL_DATABASE_USER", "PORTAL_DATABASE_PASSWORD", "DISPENSALUD_DEMO_PASSWORD",
    )
    for name in required:
        if not os.environ.get(name, "").strip():
            raise RuntimeError(f"Falta configurar {name}. No se inicia la demo.")
    certificate = Path(os.environ["DATABASE_SSL_ROOT_CERT"])
    if not certificate.is_file():
        raise RuntimeError("No se encuentra el certificado de PostgreSQL.")
    validate_jdbc_url(os.environ["DATABASE_JDBC_URL"], certificate)
    os.environ.update({
        "DJANGO_DEBUG": "0", "DISPENSALUD_HOSTED_DEMO": "1",
        "SPRING_PROFILES_ACTIVE": "cloud,demo", "API_BIND_ADDRESS": "127.0.0.1", "API_PORT": "8080",
        "DISPENSALUD_API_URL": "http://127.0.0.1:8080/api/v1",
    })
    port = int(os.environ.get("PORT", "10000"))
    if not 1024 <= port <= 65535 or port == 8080:
        raise RuntimeError("PORT no es válido para el servidor web público.")
    processes = []

    def stop(signum, frame):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        subprocess.run([sys.executable, "manage.py", "check", "--deploy", "--fail-level", "ERROR"], check=True)
        subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"], check=True)
        api = subprocess.Popen([
            "java", "-Xms48m", "-Xmx192m", "-XX:MaxMetaspaceSize=128m", "-XX:ReservedCodeCacheSize=32m",
            "-XX:+ExitOnOutOfMemoryError", "-jar", "/app/api.jar",
        ])
        processes.append(api)
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if api.poll() is not None:
                raise RuntimeError("La API no pudo iniciar. Revisa los logs del servicio.")
            try:
                with urlopen("http://127.0.0.1:8080/api/v1/health", timeout=2) as response:
                    if response.status == 200:
                        break
            except (URLError, TimeoutError, OSError):
                time.sleep(1)
        else:
            raise RuntimeError("La API no estuvo lista dentro del plazo de arranque.")
        web = subprocess.Popen([
            sys.executable, "-m", "gunicorn", "config.wsgi:application", "--bind", f"0.0.0.0:{port}",
            "--workers", "1", "--threads", "2", "--timeout", "30", "--graceful-timeout", "15",
            "--error-logfile", "-",
        ])
        processes.append(web)
        while all(process.poll() is None for process in processes):
            time.sleep(1)
        raise RuntimeError("Un componente terminó. Se detiene el contenedor para reiniciarlo completo.")
    finally:
        terminate(processes)


if __name__ == "__main__":
    main()
