import os
import secrets
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from .deployment import postgres_database, required


BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
HOSTED_DEMO = os.environ.get("DISPENSALUD_HOSTED_DEMO", "0") == "1"
REGISTRATION_ENABLED = os.environ.get("DISPENSALUD_REGISTRATION_ENABLED", "1" if DEBUG and not HOSTED_DEMO else "0") == "1"
if HOSTED_DEMO and DEBUG:
    raise ImproperlyConfigured("La demo alojada no admite DJANGO_DEBUG=1.")
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError("Configura DJANGO_SECRET_KEY antes de publicar la web.")
    key_path = DATA_DIR / "session-key"
    try:
        with key_path.open("x", encoding="utf-8") as key_file:
            key_file.write(secrets.token_urlsafe(48))
    except FileExistsError:
        pass
    SECRET_KEY = key_path.read_text(encoding="utf-8")

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",")
if HOSTED_DEMO:
    hostname = required(os.environ, "RENDER_EXTERNAL_HOSTNAME")
    ALLOWED_HOSTS = [hostname]
    CSRF_TRUSTED_ORIGINS = [f"https://{hostname}"]
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    DEMO_GATE_USER = required(os.environ, "DEMO_GATE_USER")
    DEMO_GATE_PASSWORD = required(os.environ, "DEMO_GATE_PASSWORD")
    if len(DEMO_GATE_PASSWORD) < 24:
        raise ImproperlyConfigured("DEMO_GATE_PASSWORD debe tener al menos 24 caracteres.")
    if len(SECRET_KEY) < 50:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY debe tener al menos 50 caracteres.")
INSTALLED_APPS = ["django.contrib.contenttypes", "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles", "portal"]
MIDDLEWARE = [
    "portal.middleware.BrowserSecurityMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "portal.middleware.DemoAccessMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": DATA_DIR / "sessions.sqlite3"}}
if HOSTED_DEMO:
    DATABASES = {"default": postgres_database(os.environ)}
LANGUAGE_CODE = "es-pe"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = 28800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SECURE_SSL_REDIRECT = not DEBUG
SECURE_REDIRECT_EXEMPT = [r"^salud/$"]
SECURE_HSTS_SECONDS = 3600 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
API_BASE_URL = os.environ.get("DISPENSALUD_API_URL", "http://127.0.0.1:8080/api/v1").rstrip("/")
