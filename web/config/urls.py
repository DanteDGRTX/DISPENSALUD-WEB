from django.urls import path

from portal import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("ingresar/", views.login_view, name="login"),
    path("salir/", views.logout_view, name="logout"),
    path("medicamentos/crear/", views.create_medication, name="create_medication"),
    path("horarios/crear/", views.create_schedule, name="create_schedule"),
    path("medicamentos/<uuid:medication_id>/editar/", views.update_medication, name="update_medication"),
    path("horarios/estado/", views.toggle_schedule, name="toggle_schedule"),
    path("ayuda/solicitar/", views.request_help, name="request_help"),
    path("ayuda/<uuid:request_id>/atender/", views.resolve_help, name="resolve_help"),
]
