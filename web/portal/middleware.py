import base64
import binascii
import secrets

from django.conf import settings
from django.http import HttpResponse


class DemoAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.HOSTED_DEMO or request.path == "/salud/":
            return self.get_response(request)
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Basic ") and len(authorization) <= 2048:
            try:
                username, password = base64.b64decode(authorization[6:], validate=True).decode("utf-8").split(":", 1)
                valid_user = secrets.compare_digest(username.encode(), settings.DEMO_GATE_USER.encode())
                valid_password = secrets.compare_digest(password.encode(), settings.DEMO_GATE_PASSWORD.encode())
                if valid_user and valid_password:
                    return self.get_response(request)
            except (ValueError, UnicodeDecodeError, binascii.Error):
                pass
        response = HttpResponse("Demo restringida. Solicita acceso al responsable del proyecto.", status=401, content_type="text/plain; charset=utf-8")
        response.headers["WWW-Authenticate"] = 'Basic realm="DispenSalud demo", charset="UTF-8"'
        return response


class BrowserSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
            "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
        )
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store, private"
        return response
