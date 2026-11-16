"""Firebase identity and Firestore ownership, without Admin credentials."""
import json
import re
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import jwt
from cryptography import x509
from django.conf import settings

from .errors import PhotoError

_certs, _expires, _lock = {}, 0, threading.Lock()
CERT_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")

def remote_json(url, token=None, body=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(url, data=None if body is None else json.dumps(body).encode(), headers=headers)
    try:
        with urlopen(request, timeout=4) as response:
            data = response.read(131073)
            if len(data) > 131072:
                raise PhotoError("upstream", "El servicio de identidad no está disponible.", 503)
            return json.loads(data)
    except HTTPError as error:
        if error.code in (400, 401):
            raise PhotoError("authentication", "Vuelve a iniciar sesión.", 401) from None
        if error.code in (403, 404):
            raise PhotoError("not-found", "Foto o paciente no disponible.", 404) from None
        raise PhotoError("upstream", "No se pudo conectar. Reintenta más tarde.", 503) from None
    except (URLError, TimeoutError, ValueError, OSError):
        raise PhotoError("upstream", "No se pudo conectar. Reintenta más tarde.", 503) from None

def public_key(kid):
    global _certs, _expires
    with _lock:
        if time.monotonic() >= _expires:
            _certs = remote_json(CERT_URL)
            _expires = time.monotonic() + 1800
        value = _certs.get(kid)
    if not isinstance(value, str):
        raise PhotoError("authentication", "Token no válido.", 401)
    return x509.load_pem_x509_certificate(value.encode()).public_key()

def authenticate(request):
    if request.GET:
        raise PhotoError("query", "No se admiten parámetros en esta API.")
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer ") or len(header) > 8192:
        raise PhotoError("authentication", "Inicia sesión para acceder a las fotos.", 401)
    token = header[7:]
    project = settings.FIREBASE_PROJECT_ID
    emulator = settings.DEBUG and settings.FIREBASE_EMULATORS and project == "demo-dispensalud-web"
    issuer = "https://securetoken.google.com/" + project
    try:
        if emulator:
            claims = jwt.decode(token, options={"verify_signature": False})
        else:
            head = jwt.get_unverified_header(token)
            if head.get("alg") != "RS256" or not isinstance(head.get("kid"), str):
                raise ValueError()
            claims = jwt.decode(token, public_key(head["kid"]), algorithms=["RS256"], audience=project, issuer=issuer,
                                leeway=30, options={"require": ["sub", "iat", "exp", "auth_time", "aud", "iss"]})
        now = time.time()
        uid = claims.get("sub")
        if not isinstance(uid, str) or not ID.fullmatch(uid) or claims.get("aud") != project or claims.get("iss") != issuer:
            raise ValueError()
        for name in ("iat", "exp", "auth_time"):
            if type(claims.get(name)) is not int:
                raise ValueError()
        if claims["exp"] <= now or claims["iat"] > now + 30 or claims["auth_time"] > now + 30 or claims["exp"] - claims["iat"] > 3700:
            raise ValueError()
    except PhotoError:
        raise
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise PhotoError("authentication", "La sesión no es válida o ha caducado.", 401) from None
    if claims.get("email_verified") is not True:
        raise PhotoError("verification", "Verifica tu correo para usar las fotos.", 403)
    auth_base = "http://127.0.0.1:9098/identitytoolkit.googleapis.com" if emulator else "https://identitytoolkit.googleapis.com"
    account = remote_json(auth_base + "/v1/accounts:lookup?key=" + quote(settings.FIREBASE_WEB_API_KEY, safe=""), body={"idToken": token})
    users = account.get("users", [])
    if len(users) != 1 or users[0].get("localId") != uid or users[0].get("disabled") or not users[0].get("emailVerified"):
        raise PhotoError("authentication", "Vuelve a iniciar sesión.", 401)
    if int(users[0].get("validSince", 0)) > claims["auth_time"]:
        raise PhotoError("authentication", "La sesión fue revocada.", 401)
    return uid, token

def authorize_patient(uid, token, patient_id, allow_deleted=False):
    if not ID.fullmatch(patient_id) or patient_id.lower().startswith("demo-"):
        raise PhotoError("not-found", "Paciente no disponible.", 404)
    base = "http://127.0.0.1:8089" if settings.DEBUG and settings.FIREBASE_EMULATORS else "https://firestore.googleapis.com"
    path = "/v1/projects/" + settings.FIREBASE_PROJECT_ID + "/databases/(default)/documents/users/" + quote(uid, safe="") + "/patients/" + quote(patient_id, safe="")
    fields = remote_json(base + path, token=token).get("fields", {})
    deleted = fields.get("deleted", {}).get("booleanValue")
    if fields.get("ownerUid", {}).get("stringValue") != uid or fields.get("id", {}).get("stringValue") != patient_id or not (deleted is False or allow_deleted and deleted is True):
        raise PhotoError("not-found", "Paciente no disponible.", 404)
