import hashlib
from io import BytesIO
import os
from pathlib import Path
import sqlite3
import tempfile
import time
import uuid
import warnings

from django.conf import settings
from PIL import Image, ImageOps, PngImagePlugin, UnidentifiedImageError
from .errors import PhotoError

MAX_UPLOAD = 2 * 1024 * 1024
MAX_OUTPUT = 128 * 1024
Image.MAX_IMAGE_PIXELS = 4194304
PngImagePlugin.MAX_TEXT_CHUNK = 65536
PngImagePlugin.MAX_TEXT_MEMORY = 262144

def normalize(content, mime):
    if not content or len(content) > MAX_UPLOAD:
        raise PhotoError("size", "Elige una imagen de hasta 2 MiB.", 413)
    allowed = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}
    if mime not in allowed:
        raise PhotoError("format", "Usa JPEG, PNG o WebP sin animación.", 415)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as check:
                if check.format != allowed[mime] or getattr(check, "n_frames", 1) != 1:
                    raise PhotoError("format", "El contenido no corresponde a un formato permitido.", 415)
                width, height = check.size
                if max(width, height) > 4096 or width * height > 4194304:
                    raise PhotoError("dimensions", "La imagen supera el límite de dimensiones.", 422)
                check.verify()
            with Image.open(BytesIO(content)) as source:
                source = ImageOps.exif_transpose(source)
                source.thumbnail((512, 512), Image.Resampling.LANCZOS)
                rgba = source.convert("RGBA")
                result = Image.new("RGB", rgba.size, (16, 38, 61))
                result.paste(rgba, mask=rgba.getchannel("A"))
                for quality in (82, 70, 55):
                    output = BytesIO()
                    result.save(output, "JPEG", quality=quality)
                    if output.tell() <= MAX_OUTPUT:
                        return output.getvalue()
        raise PhotoError("size", "No se pudo comprimir esta imagen.", 422)
    except PhotoError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise PhotoError("image", "La imagen está dañada o no es válida.", 422) from None

class PhotoStore:
    def __init__(self):
        self.root = Path(settings.PRIVATE_PHOTO_ROOT)
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "index.sqlite3", timeout=2)
        self.db.row_factory = sqlite3.Row
        self.db.execute("CREATE TABLE IF NOT EXISTS photos (uid TEXT, subject TEXT, photo TEXT, etag TEXT NOT NULL, size INTEGER NOT NULL, mutation TEXT, digest TEXT, updated REAL NOT NULL, PRIMARY KEY(uid,subject))")

    def close(self):
        self.db.close()

    def row(self, uid, subject):
        return self.db.execute("SELECT * FROM photos WHERE uid=? AND subject=?", (uid, subject)).fetchone()

    @staticmethod
    def metadata(subject, row):
        photo = row["photo"] if row else None
        return {"subject": subject, "state": "ready" if photo else "deleted" if row else "empty", "photoId": photo,
                "reference": "private-photo:v1:" + photo if photo else None, "etag": row["etag"] if row else "none"}

    def path(self, uid, photo):
        directory = self.root / hashlib.sha256(uid.encode()).hexdigest()
        if directory.is_symlink():
            raise PhotoError("storage", "Almacenamiento no disponible.", 503)
        directory.mkdir(mode=0o700, exist_ok=True)
        return directory / (photo + ".jpg")

    def change(self, uid, subject, etag, image=None, mutation=None, source_digest=None):
        if not etag:
            raise PhotoError("precondition", "Actualiza la foto antes de guardar.", 428)
        new_path = None
        try:
            self.db.execute("BEGIN IMMEDIATE")
            old = self.row(uid, subject)
            if not old and (self.db.execute("SELECT COUNT(*) FROM photos WHERE uid=?", (uid,)).fetchone()[0] >= 256 or self.db.execute("SELECT COUNT(*) FROM photos").fetchone()[0] >= 4096):
                raise PhotoError("quota", "Se alcanzó el límite de referencias de fotos.", 507)
            if image is not None and old and old["mutation"] == mutation:
                if old["digest"] != source_digest:
                    raise PhotoError("conflict", "La clave de reintento corresponde a otra imagen.", 409)
                self.db.rollback()
                return self.metadata(subject, old)
            if etag != (old["etag"] if old else "none"):
                raise PhotoError("conflict", "Otra sesión cambió la foto. Actualiza antes de continuar.", 409)
            size = len(image) if image is not None else 0
            old_size = old["size"] if old else 0
            total = self.db.execute("SELECT COALESCE(SUM(size),0) FROM photos").fetchone()[0]
            own, count = self.db.execute("SELECT COALESCE(SUM(size),0),COUNT(photo) FROM photos WHERE uid=?", (uid,)).fetchone()
            if image is not None and (total - old_size + size > settings.PRIVATE_PHOTO_TOTAL_BYTES or own - old_size + size > settings.PRIVATE_PHOTO_UID_BYTES or count + (0 if old and old["photo"] else 1) > settings.PRIVATE_PHOTO_UID_COUNT):
                raise PhotoError("quota", "Se alcanzó el límite de fotos. Elimina una foto compartida antes de subir otra.", 507)
            photo = uuid.uuid4().hex if image is not None else None
            next_etag = photo or uuid.uuid4().hex
            if image is not None:
                new_path = self.path(uid, photo)
                temporary = None
                try:
                    with tempfile.NamedTemporaryFile(dir=new_path.parent, delete=False) as stream:
                        temporary = Path(stream.name)
                        stream.write(image)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temporary, new_path)
                finally:
                    if temporary and temporary.exists():
                        temporary.unlink()
            self.db.execute("INSERT OR REPLACE INTO photos VALUES (?,?,?,?,?,?,?,?)", (uid, subject, photo, next_etag, size, mutation, source_digest, time.time()))
            self.db.commit()
        except Exception:
            self.db.rollback()
            if new_path:
                new_path.unlink(missing_ok=True)
            raise
        if old and old["photo"]:
            try:
                self.path(uid, old["photo"]).unlink(missing_ok=True)
            except OSError:
                pass  # bounded orphan cleanup, never undo a committed new version
        return self.metadata(subject, self.row(uid, subject))

    def cleanup(self, apply=False, age=3600):
        live = {self.path(row["uid"], row["photo"]) for row in self.db.execute("SELECT uid,photo FROM photos WHERE photo IS NOT NULL")}
        candidates = [path for directory in self.root.iterdir() if directory.is_dir() and not directory.is_symlink()
                      for path in directory.iterdir() if path.is_file() and not path.is_symlink() and path not in live and path.stat().st_mtime < time.time() - age][:100]
        if apply:
            for path in candidates:
                path.unlink(missing_ok=True)
        return len(candidates)
