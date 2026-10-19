from functools import wraps
from urllib.parse import urlencode

from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.cache import add_never_cache_headers
from django.utils.dateparse import parse_datetime
from django.middleware.csrf import rotate_token
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from .api import ApiError, request_api
from .forms import IdentityForm, LoginForm, MedicationForm, ScheduleForm, ScheduleToggleForm


def authenticated(view):
    @wraps(view)
    def wrapper(request, *arguments, **keywords):
        token = request.session.get("api_token")
        if not token:
            return redirect("login")
        try:
            request.account = request_api("/me", token)
            response = view(request, *arguments, **keywords)
            add_never_cache_headers(response)
            return response
        except ApiError as error:
            if error.status == 401:
                request.session.flush()
                messages.info(request, "Vuelve a ingresar para continuar.")
                return redirect("login")
            return render(request, "portal/error.html", {"detail": str(error)}, status=error.status)
    return wrapper


@require_http_methods(["GET", "POST"])
@never_cache
def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            result = request_api("/auth/sessions", method="POST", data=form.cleaned_data)
            request.session.flush()
            rotate_token(request)
            request.session["api_token"] = result["token"]
            request.session.set_expiry(28800)
            return redirect("dashboard")
        except ApiError as error:
            form.add_error(None, str(error))
    return render(request, "portal/login.html", {"form": form})


@require_POST
def logout_view(request):
    token = request.session.get("api_token")
    if token:
        try:
            request_api("/auth/sessions/current", token, method="DELETE")
        except ApiError:
            pass
    request.session.flush()
    return redirect("login")


@require_http_methods(["GET"])
@authenticated
def dashboard(request):
    token = request.session["api_token"]
    people = request_api("/people", token)
    person_id = request.GET.get("person", people[0]["id"] if people else "")
    selected = next((person for person in people if person["id"] == person_id), None)
    if person_id and selected is None:
        return HttpResponseForbidden("No tienes acceso a esta persona.")
    medications = request_api(f"/people/{person_id}/medications", token) if selected else []
    plan = request_api(f"/people/{person_id}/today", token) if selected else {"doses": []}
    schedules = request_api(f"/people/{person_id}/schedules", token) if selected else []
    history = request_api(f"/people/{person_id}/history", token) if selected else []
    help_requests = request_api(f"/people/{person_id}/help-requests", token) if selected else []
    action_labels = {
        "MEDICATION_CREATED": "Medicamento registrado", "MEDICATION_UPDATED": "Indicación actualizada",
        "SCHEDULE_CREATED": "Horario creado", "SCHEDULE_PAUSED": "Horario pausado",
        "SCHEDULE_RESUMED": "Horario reactivado", "HELP_REQUESTED": "Solicitud de ayuda",
        "HELP_RESOLVED": "Solicitud atendida",
    }
    for event in history:
        event["label"] = action_labels.get(event["action"], "Cambio registrado")
        event["when"] = parse_datetime(event["occurredAt"])
    for help_request in help_requests:
        help_request["when"] = parse_datetime(help_request["createdAt"])
    preview = request.account["role"] == "CAREGIVER" and request.GET.get("preview") == "1"
    adult_mode = request.account["role"] == "OLDER_ADULT" or preview
    section = request.GET.get("vista", "hoy")
    allowed_sections = {"hoy", "medicamentos", "ayuda"} if adult_mode else {"hoy", "medicamentos", "actividad"}
    if section not in allowed_sections:
        section = "hoy"
    editing = next((medication for medication in medications if medication["id"] == request.GET.get("editar")), None)
    initial = {"person_id": person_id}
    if editing:
        initial.update({"name": editing["name"], "instructions": editing["instructions"]})
    now = timezone.localtime()
    upcoming = next((dose for dose in plan["doses"] if dose["localTime"] >= now.strftime("%H:%M:%S")), None)
    search = request.GET.get("q", "").strip()[:120]
    visible_medications = [medication for medication in medications if search.casefold() in medication["name"].casefold()]
    context = {
        "account": request.account, "people": people, "selected": selected,
        "medications": medications, "plan": plan,
        "medication_form": MedicationForm(initial=initial, auto_id="medicine_%s"),
        "create_form": MedicationForm(initial={"person_id": person_id}, auto_id="create_%s"),
        "schedule_form": ScheduleForm(initial={"person_id": person_id, "start_date": timezone.localdate()}, auto_id="schedule_%s"),
        "schedules": schedules, "history": history, "help_requests": help_requests,
        "open_requests": [item for item in help_requests if item["status"] == "OPEN"],
        "active_schedules": sum(1 for item in schedules if item["enabled"]),
        "section": section, "adult_mode": adult_mode, "preview": preview,
        "upcoming": upcoming, "now": now, "editing": editing,
        "greeting_name": selected["displayName"].removesuffix(" (persona ficticia)") if selected else request.account["displayName"],
        "visible_medications": visible_medications, "search": search,
    }
    template = "portal/adult.html" if adult_mode else "portal/caregiver.html"
    return render(request, template, context)


def return_to_person(person_id, section="medicamentos"):
    return redirect(f"{reverse('dashboard')}?{urlencode({'person': person_id, 'vista': section})}")


@require_POST
@authenticated
def create_medication(request):
    if request.account["role"] != "CAREGIVER":
        return HttpResponseForbidden("Sólo el cuidador puede configurar medicamentos.")
    form = MedicationForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Revisa el nombre y la indicación del medicamento.")
        return redirect("dashboard")
    data = form.cleaned_data
    try:
        request_api(f"/people/{data['person_id']}/medications", request.session["api_token"], method="POST",
            data={"name": data["name"], "instructions": data["instructions"]})
        messages.success(request, "Medicamento registrado. Ahora puedes agregar su horario.")
    except ApiError as error:
        messages.error(request, str(error))
    return return_to_person(str(data["person_id"]))


@require_POST
@authenticated
def create_schedule(request):
    if request.account["role"] != "CAREGIVER":
        return HttpResponseForbidden("Sólo el cuidador puede configurar horarios.")
    form = ScheduleForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Revisa el medicamento, la hora y las fechas.")
        return redirect("dashboard")
    data = form.cleaned_data
    try:
        request_api(f"/people/{data['person_id']}/schedules", request.session["api_token"], method="POST", data={
            "medicationId": str(data["medication_id"]), "localTime": data["local_time"].isoformat(),
            "startDate": data["start_date"].isoformat(),
            "endDate": data["end_date"].isoformat() if data["end_date"] else None,
        })
        messages.success(request, "Horario diario guardado.")
    except ApiError as error:
        messages.error(request, str(error))
    return return_to_person(str(data["person_id"]))


@require_POST
@authenticated
def update_medication(request, medication_id):
    if request.account["role"] != "CAREGIVER":
        return HttpResponseForbidden("Sólo el cuidador puede configurar medicamentos.")
    form = MedicationForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Completa el nombre y la indicación, respetando el largo permitido.")
        return redirect("dashboard")
    data = form.cleaned_data
    request_api(f"/people/{data['person_id']}/medications/{medication_id}", request.session["api_token"], method="PUT",
        data={"name": data["name"], "instructions": data["instructions"]})
    messages.success(request, "Indicación actualizada y guardada en el historial.")
    return return_to_person(str(data["person_id"]))


@require_POST
@authenticated
def toggle_schedule(request):
    if request.account["role"] != "CAREGIVER":
        return HttpResponseForbidden("Sólo el cuidador puede configurar horarios.")
    form = ScheduleToggleForm(request.POST)
    if not form.is_valid():
        messages.error(request, "No pudimos identificar el horario.")
        return redirect("dashboard")
    data = form.cleaned_data
    request_api(f"/people/{data['person_id']}/schedules/{data['schedule_id']}", request.session["api_token"],
        method="PATCH", data={"enabled": data["enabled"]})
    messages.success(request, "Horario reactivado." if data["enabled"] else "Horario pausado. Ya no aparece en el plan diario.")
    return return_to_person(str(data["person_id"]))


@require_POST
@authenticated
def request_help(request):
    if request.account["role"] != "OLDER_ADULT":
        return HttpResponseForbidden("La solicitud debe hacerla la persona usuaria desde su cuenta.")
    person_id = request.account["id"]
    request_api(f"/people/{person_id}/help-requests", request.session["api_token"], method="POST")
    messages.success(request, "Tu solicitud quedó registrada en el panel de tu cuidador.")
    return return_to_person(person_id, "ayuda")


@require_POST
@authenticated
def resolve_help(request, request_id):
    if request.account["role"] != "CAREGIVER":
        return HttpResponseForbidden("Sólo el cuidador puede atender esta solicitud.")
    form = IdentityForm(request.POST)
    if not form.is_valid():
        return HttpResponseForbidden("Persona no válida.")
    person_id = str(form.cleaned_data["person_id"])
    request_api(f"/people/{person_id}/help-requests/{request_id}", request.session["api_token"], method="PATCH")
    messages.success(request, "Solicitud marcada como atendida.")
    return return_to_person(person_id, "actividad")
