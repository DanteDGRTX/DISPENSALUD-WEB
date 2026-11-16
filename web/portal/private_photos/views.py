import hashlib
import os
import re
import sqlite3
import uuid
from functools import wraps

from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .errors import PhotoError
from .identity import authenticate, authorize_patient
from .store import MAX_UPLOAD, PhotoStore, normalize

PHOTO_ID = re.compile(r"[a-f0-9]{32}\Z")

def endpoint(function):
    @csrf_exempt
    @wraps(function)
    def guarded(request, **kwargs):
        store = None
        try:
            if request.method not in ("GET", "PUT", "DELETE"):
                raise PhotoError("method", "Método no permitido.", 405)
            origin = request.headers.get("Origin")
            if origin and origin != request.scheme + "://" + request.get_host():
                raise PhotoError("origin", "Origen no permitido.", 403)
            uid, token = authenticate(request)
            store = PhotoStore()
            response = function(request, store, uid, token, **kwargs)
        except PhotoError as error:
            response = JsonResponse({"error": {"code": error.code, "message": error.message}}, status=error.status)
        except Exception:
            # Never serialize exceptions, request bodies, filenames or bearer tokens.
            response = JsonResponse({"error": {"code": "unavailable", "message": "No se pudo completar la operación. Reintenta."}}, status=503)
        finally:
            if store:
                store.close()
        response["Cache-Control"] = "no-store, private"
        response["Vary"] = "Authorization"
        response["X-Content-Type-Options"] = "nosniff"
        if response.status_code == 401:
            response["WWW-Authenticate"] = "Bearer"
        return response
    return guarded

@endpoint
def index(request, store, uid, token):
    if request.method != "GET":
        raise PhotoError("method", "Método no permitido.", 405)
    rows = store.db.execute("SELECT * FROM photos WHERE uid=?", (uid,)).fetchall()
    return JsonResponse({"photos": [store.metadata(row["subject"], row) for row in rows]})

@endpoint
def subject(request, store, uid, token, patient_id=None):
    name = "profile"
    if patient_id is not None:
        authorize_patient(uid, token, patient_id, allow_deleted=request.method == "DELETE")
        name = "patient:" + patient_id
    if request.method == "GET":
        return JsonResponse(store.metadata(name, store.row(uid, name)))
    etag = request.headers.get("If-Match", "").strip('"')
    if request.method == "DELETE":
        return JsonResponse(store.change(uid, name, etag))
    try:
        size = int(request.headers.get("Content-Length", 0))
    except ValueError:
        size = 0
    if size <= 0 or size > MAX_UPLOAD:
        raise PhotoError("size", "Elige una imagen de hasta 2 MiB.", 413)
    mutation = request.headers.get("Idempotency-Key", "")
    try:
        uuid.UUID(mutation)
    except ValueError:
        raise PhotoError("mutation", "Falta un identificador de subida válido.") from None
    content = request.read(MAX_UPLOAD + 1)
    if len(content) != size:
        raise PhotoError("size", "No se recibió la imagen completa.", 413)
    image = normalize(content, request.content_type)
    return JsonResponse(store.change(uid, name, etag, image, mutation, hashlib.sha256(content).hexdigest()))

@endpoint
def file(request, store, uid, token, photo_id):
    if request.method != "GET":
        raise PhotoError("method", "Método no permitido.", 405)
    if not PHOTO_ID.fullmatch(photo_id):
        raise PhotoError("not-found", "Foto no disponible.", 404)
    row = store.db.execute("SELECT * FROM photos WHERE uid=? AND photo=?", (uid, photo_id)).fetchone()
    if not row:
        raise PhotoError("not-found", "Foto no disponible.", 404)
    if row["subject"].startswith("patient:"):
        authorize_patient(uid, token, row["subject"][8:])
    path = store.path(uid, photo_id)
    if not path.is_file() or path.is_symlink():
        raise PhotoError("not-found", "Foto no disponible.", 404)
    stream = os.fdopen(os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)), "rb")
    return FileResponse(stream, content_type="image/jpeg", filename="avatar.jpg")
