from unittest.mock import patch

from django.test import Client, TestCase, override_settings
from .forms import RegistrationForm


@override_settings(ROOT_URLCONF="config.legacy_urls")
class ProductIntegrationTests(TestCase):
    def test_home_preserves_product_presentation_and_separate_account(self):
        response = self.client.get("/")
        self.assertContains(response, "PillBox")
        self.assertContains(response, 'href="/ingresar/"')
        self.assertContains(response, 'id="galeria"')
        self.assertNotContains(response, "Datos ficticios")
        self.assertNotContains(response, "Versión de evaluación")
        self.assertNotContains(response, "fonts.googleapis")

    def test_account_registration_has_no_repeated_evaluation_badge(self):
        response = self.client.get("/cuenta/crear/")
        self.assertNotContains(response, "versión es de evaluación")
        self.assertContains(response, "mantendré mi contraseña privada")

    def test_account_page_does_not_request_role_as_authorization(self):
        response = self.client.get("/ingresar/?perfil=cuidador")
        self.assertContains(response, "Acceso del cuidador")
        self.assertNotContains(response, 'name="role"')

    @override_settings(REGISTRATION_ENABLED=False)
    @patch("portal.views.request_api")
    def test_registration_closed_environment_cannot_submit_directly(self, api):
        self.assertContains(self.client.get("/cuenta/crear/"), "El registro está cerrado")
        self.assertEqual(self.client.post("/cuenta/crear/", {}).status_code, 403)
        api.assert_not_called()

    @override_settings(REGISTRATION_ENABLED=True)
    @patch("portal.views.request_api", return_value={"id": "test-account"})
    def test_registration_creates_account_without_granting_links_or_session(self, api):
        response = self.client.post("/cuenta/crear/", {"display_name": "Persona de prueba", "username": "Persona.Nueva",
            "role": "OLDER_ADULT", "password": "Test-only-password-2026", "password_confirmation": "Test-only-password-2026", "accept": "on"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/ingresar/")
        self.assertNotIn("api_token", self.client.session)
        self.assertEqual(api.call_args.kwargs["data"]["username"], "persona.nueva")
        self.assertNotIn("person_id", api.call_args.kwargs["data"])

    def test_registration_rejects_missing_consent_mismatch_and_privileged_role(self):
        form = RegistrationForm({"display_name": "Test", "username": "test", "role": "ADMIN",
            "password": "Test-only-password", "password_confirmation": "other"})
        self.assertFalse(form.is_valid())
        self.assertIn("accept", form.errors)
        self.assertIn("role", form.errors)
        self.assertIn("password_confirmation", form.errors)

    def test_registration_requires_csrf(self):
        self.assertEqual(Client(enforce_csrf_checks=True).post("/cuenta/crear/", {}).status_code, 403)

    def test_old_dashboard_bookmark_redirects_only_to_local_panel(self):
        session = self.client.session
        session["api_token"] = "test-token"
        session.save()
        response = self.client.get("/?person=test&vista=hoy")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].startswith("/panel/?"))
