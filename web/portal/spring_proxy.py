"""Same-origin, fixed-destination bridge. Spring alone validates Firebase identity."""
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

ROUTES = {"workspace": {"GET"}, "patients": {"POST"}, "patients/delete": {"POST"}, "supervision": {"POST"}}

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None

@csrf_exempt
def forward(request, endpoint):
    if not settings.SPRING_API_URL:
        return JsonResponse({"error": "La gestión adicional no está habilitada."}, status=404)
    if endpoint not in ROUTES or request.method not in ROUTES[endpoint] or request.GET:
        return JsonResponse({"error": "Ruta o método no permitido."}, status=405)
    origin = request.headers.get("Origin")
    if origin and origin != request.scheme + "://" + request.get_host():
        return JsonResponse({"error": "Origen no permitido."}, status=403)
    authorization = request.headers.get("Authorization", "")
    if len(authorization) > 8192 or not re.fullmatch(r"Bearer [A-Za-z0-9._~-]+", authorization):
        return JsonResponse({"error": "Inicia sesión para continuar."}, status=401)
    body = None
    headers = {"Authorization": authorization, "Accept": "text/html,application/json"}
    if request.method == "POST":
        if request.content_type != "application/x-www-form-urlencoded":
            return JsonResponse({"error": "Formato no permitido."}, status=415)
        try:
            size = int(request.headers.get("Content-Length", "0"))
        except ValueError:
            size = -1
        if size < 0 or size > 65536:
            return JsonResponse({"error": "Formulario demasiado grande."}, status=413)
        body = request.read(65537)
        if len(body) > 65536 or len(body) != size:
            return JsonResponse({"error": "Formulario no válido."}, status=413)
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    upstream = Request(settings.SPRING_API_URL + "/" + endpoint, data=body, headers=headers, method=request.method)
    try:
        opener = build_opener(ProxyHandler({}), NoRedirect())
        try:
            remote = opener.open(upstream, timeout=12)
        except HTTPError as error:
            remote = error
        with remote:
            payload = remote.read(1048577)
            if len(payload) > 1048576 or 300 <= remote.code < 400:
                raise ValueError()
            content_type = remote.headers.get("Content-Type", "").split(";")[0]
            if content_type not in ("text/html", "application/json"):
                raise ValueError()
            response = HttpResponse(payload, status=remote.code, content_type=content_type + "; charset=utf-8")
    except (URLError, TimeoutError, OSError, ValueError):
        response = JsonResponse({"error": "El servicio de gestión no está disponible. Tus datos siguen guardados."}, status=503)
    response["Cache-Control"] = "no-store, private"
    response["Vary"] = "Authorization"
    return response
