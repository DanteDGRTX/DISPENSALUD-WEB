from unittest.mock import patch
from datetime import date
from uuid import uuid4

from django.test import Client, TestCase
from .forms import ScheduleForm


class PortalAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.person_id = str(uuid4())

    def sign_in_session(self):
        session = self.client.session
        session["api_token"] = "test-token"
        session.save()

    def test_login_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post("/ingresar/", {"username": "adult", "password": "test"})
        self.assertEqual(response.status_code, 403)

    def test_schedule_date_initial_uses_browser_date_format(self):
        form = ScheduleForm(initial={"start_date": date(2026, 10, 17)})
        self.assertIn('value="2026-10-17"', str(form["start_date"]))

    def test_anonymous_visits_redirect_to_login(self):
        self.assertRedirects(self.client.get("/"), "/ingresar/", fetch_redirect_response=False)

    @patch("portal.views.request_api")
    def test_older_adult_direct_configuration_post_is_forbidden(self, api):
        self.sign_in_session()
        api.return_value = {"id": self.person_id, "role": "OLDER_ADULT", "displayName": "Test adult"}
        response = self.client.post("/medicamentos/crear/", {})
        self.assertEqual(response.status_code, 403)
        api.assert_called_once_with("/me", "test-token")

    @patch("portal.views.request_api")
    def test_adult_dashboard_has_no_configuration_form(self, api):
        self.sign_in_session()
        api.side_effect = [
            {"id": self.person_id, "role": "OLDER_ADULT", "displayName": "Test adult"},
            [{"id": self.person_id, "displayName": "Test adult"}], [], {"doses": []}, [], [], [],
        ]
        response = self.client.get("/")
        self.assertContains(response, "Mi horario de hoy")
        self.assertNotContains(response, "Agregar medicamento")

    @patch("portal.views.request_api")
    def test_dashboard_cannot_select_unlinked_person(self, api):
        self.sign_in_session()
        api.side_effect = [
            {"id": str(uuid4()), "role": "CAREGIVER", "displayName": "Test caregiver"},
            [{"id": self.person_id, "displayName": "Test adult"}],
        ]
        response = self.client.get("/", {"person": str(uuid4())})
        self.assertEqual(response.status_code, 403)

    @patch("portal.views.request_api")
    def test_caregiver_preview_does_not_switch_identity_or_enable_help_submission(self, api):
        self.sign_in_session()
        account = {"id": str(uuid4()), "role": "CAREGIVER", "displayName": "Caregiver"}
        api.side_effect = [account, [{"id": self.person_id, "displayName": "Test adult"}], [], {"doses": []}, [], [], []]
        response = self.client.get("/", {"preview": "1", "vista": "ayuda"})
        self.assertContains(response, "Vista previa")
        self.assertNotContains(response, 'action="/ayuda/solicitar/"')
        api.side_effect = None
        api.return_value = account
        self.assertEqual(self.client.post("/ayuda/solicitar/").status_code, 403)

    @patch("portal.views.request_api")
    def test_schedule_pause_submits_boolean_false_to_api(self, api):
        self.sign_in_session()
        api.side_effect = [{"role": "CAREGIVER"}, {"enabled": False}]
        schedule_id = str(uuid4())
        response = self.client.post("/horarios/estado/", {"person_id": self.person_id, "schedule_id": schedule_id, "enabled": "false"})
        self.assertEqual(response.status_code, 302)
        api.assert_called_with(f"/people/{self.person_id}/schedules/{schedule_id}", "test-token", method="PATCH", data={"enabled": False})
