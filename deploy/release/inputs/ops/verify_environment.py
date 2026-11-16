"""Fail closed before Gunicorn starts; no secret values are printed."""
import os
from pathlib import Path
import sys

def require(condition, message):
    if not condition:
        raise SystemExit(message)

require(sys.platform == "linux", "Target runtime must be Linux.")
require(sys.version_info[:3] == (3, 14, 4), "Review target Python version before starting this release.")
require(os.environ.get("DJANGO_DEBUG") == "0", "DJANGO_DEBUG must be 0.")
require(os.environ.get("DISPENSALUD_HOSTED_DEMO") == "0", "Legacy hosted demo must be disabled.")
require(os.environ.get("DISPENSALUD_FIREBASE_EMULATORS") == "0", "Emulators must be disabled.")
require(os.environ.get("DJANGO_DATA_DIR") == "/srv/dispensalud-web/shared", "Unexpected persistent data directory.")
require(len(os.environ.get("DJANGO_SECRET_KEY", "")) >= 50, "A server-generated Django key is required.")
release = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(release / "web"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
from django.conf import settings

hosts = {"app.dispensalud.site", "www.dispensalud.site", "dispensalud.site"}
require(not settings.DEBUG and not settings.FIREBASE_EMULATORS and not settings.HOSTED_DEMO, "Unexpected runtime mode.")
require(set(settings.ALLOWED_HOSTS) == hosts, "Allowed hosts must match the three reviewed hosts.")
require(set(settings.CSRF_TRUSTED_ORIGINS) == {"https://" + host for host in hosts}, "Unexpected CSRF origins.")
require(settings.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https"), "HTTPS proxy configuration missing.")
require(settings.SECURE_SSL_REDIRECT and settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE, "Secure cookies/HTTPS required.")
require(settings.SESSION_COOKIE_HTTPONLY and settings.SESSION_COOKIE_SAMESITE == "Lax", "Unexpected session cookie policy.")
require(not settings.SECURE_HSTS_INCLUDE_SUBDOMAINS and not settings.SECURE_HSTS_PRELOAD, "Do not extend HSTS to AgroSmart hosts.")
require(settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3", "Unexpected database backend.")
for asset in ("portal/firebase/app.js", "portal/firebase/panel-web.css", "portal/firebase/app.css", "portal/product/integration.css"):
    require((settings.STATIC_ROOT / asset).is_file(), "Missing prebuilt static asset: " + asset)
print("Production environment checks passed; no secret values displayed.")
