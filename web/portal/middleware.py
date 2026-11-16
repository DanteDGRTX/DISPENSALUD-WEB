from django.conf import settings


class BrowserSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        firebase_connections = " https://identitytoolkit.googleapis.com https://securetoken.googleapis.com https://firestore.googleapis.com"
        if settings.FIREBASE_EMULATORS:
            firebase_connections += " http://127.0.0.1:9098 http://127.0.0.1:8089 http://localhost:9098 http://localhost:8089"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' blob: data:; font-src 'self'; connect-src 'self'" + firebase_connections + "; "
            "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
        )
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store, private"
        return response
