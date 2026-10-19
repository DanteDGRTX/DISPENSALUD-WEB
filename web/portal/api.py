import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class ApiError(Exception):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


def request_api(path, token=None, method="GET", data=None, timeout=8):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        payload = json.dumps(data).encode("utf-8")
    request = Request(f"{settings.API_BASE_URL}{path}", data=payload, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
            return json.loads(body) if body else None
    except HTTPError as error:
        try:
            detail = json.loads(error.read()).get("message", "No se pudo completar la operación.")
        except (ValueError, AttributeError):
            detail = "No se pudo completar la operación."
        raise ApiError(error.code, detail) from error
    except (URLError, TimeoutError, OSError) as error:
        raise ApiError(503, "No podemos conectar con el servicio. Inténtalo de nuevo en un momento.") from error
