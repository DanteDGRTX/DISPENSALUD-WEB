from django.urls import path

from portal import views, firebase_views as firebase


urlpatterns = [
    path("salud/", firebase.health, name="health"),
    path("", views.home, name="home"),
    path("panel/", firebase.shell, name="dashboard"),
    path("cuenta/crear/", firebase.shell, {"page":"register"}, name="register"),
    path("ingresar/", firebase.shell, {"page":"login"}, name="login"),
    path("cuenta/recuperar/", firebase.shell, {"page":"reset"}, name="reset"),
    path("cuenta/verificar/", firebase.shell, {"page":"verify"}, name="verify"),
    path("salir/", firebase.shell, {"page":"logout"}, name="logout"),
    path("pacientes/", firebase.shell, {"page":"patients"}, name="patients"),
    path("tratamientos/", firebase.shell, {"page":"treatments"}, name="treatments"),
    path("historial/", firebase.shell, {"page":"history"}, name="history"),
    path("alertas/", firebase.shell, {"page":"alerts"}, name="alerts"),
    path("equipo/", firebase.shell, {"page":"device"}, name="device"),
    path("perfil/", firebase.shell, {"page":"profile"}, name="profile"),
]
