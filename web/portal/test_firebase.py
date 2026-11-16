from unittest.mock import patch
from django.test import SimpleTestCase, override_settings
from django.urls import resolve, Resolver404


class FirebaseShellTests(SimpleTestCase):
    @patch("portal.views.request_api", side_effect=AssertionError("No Spring Boot"))
    def test_real_routes_are_public_shells_without_business_data_or_legacy_auth(self, api):
        for path in ("/ingresar/", "/cuenta/crear/", "/cuenta/recuperar/", "/cuenta/verificar/", "/panel/", "/pacientes/", "/tratamientos/", "/historial/", "/alertas/", "/equipo/", "/perfil/", "/salir/"):
            response = self.client.get(path)
            self.assertContains(response, 'portal/firebase/app.js')
            self.assertNotContains(response, 'api_token')
            self.assertIn('no-store', response.headers['Cache-Control'])
        api.assert_not_called()

    def test_old_business_endpoints_and_demo_are_unreachable(self):
        for path in ("/medicamentos/crear/", "/horarios/crear/", "/demo/"):
            with self.assertRaises(Resolver404):
                resolve(path)

    def test_no_credentials_or_uid_server_endpoint(self):
        self.assertEqual(self.client.post('/ingresar/', {'uid': 'other', 'password':'fake'}).status_code, 405)
        self.assertEqual(self.client.get('/salud/').json(), {'status':'ok'})

    def test_csp_allows_only_required_firebase_services(self):
        policy=self.client.get('/ingresar/').headers['Content-Security-Policy']
        self.assertIn('https://firestore.googleapis.com', policy)
        self.assertIn("script-src 'self'", policy)
        self.assertNotIn('unsafe-inline', policy)
        self.assertNotIn('9098', policy)

    @override_settings(FIREBASE_EMULATORS=True)
    def test_emulator_mode_is_explicit(self):
        response=self.client.get('/ingresar/')
        self.assertContains(response, '"emulators": true')
        self.assertIn('http://127.0.0.1:9098', response.headers['Content-Security-Policy'])

    def test_landing_uses_copied_assets_and_current_scope(self):
        response=self.client.get('/')
        self.assertContains(response, 'firebase/assets/pillbox_pro.webp')
        self.assertContains(response, 'Firebase')
        self.assertNotContains(response, 'se ejecuta en Render')
