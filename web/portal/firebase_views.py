"""Public shells. Private data is authorized by Firebase; no UID-based server endpoints."""
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@require_GET
@never_cache
def shell(request, page="panel"):
    return render(request, "portal/firebase.html", {"page": page, "runtime": {"emulators": settings.FIREBASE_EMULATORS, "springEnabled": bool(settings.SPRING_API_URL)}})


@require_GET
def health(request):
    # A liveness probe requires neither elevated Firebase access nor Spring Boot.
    return JsonResponse({"status": "ok"})

