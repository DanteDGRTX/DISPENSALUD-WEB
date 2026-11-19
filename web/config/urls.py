from django.urls import path

from portal import views, firebase_views as firebase
from portal.private_photos import views as photos
from portal import spring_proxy


urlpatterns = [
    path("gestion/", firebase.shell, {"page": "spring"}, name="spring_management"),
    path("api/spring/<path:endpoint>", spring_proxy.forward),
    path("api/photos/v1/", photos.index),
    path("api/photos/v1/profile/", photos.subject),
    path("api/photos/v1/patients/<str:patient_id>/", photos.subject),
    path("api/photos/v1/files/<str:photo_id>/", photos.file),
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

