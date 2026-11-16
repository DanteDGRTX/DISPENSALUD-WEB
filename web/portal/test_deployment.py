from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError
from django.test import SimpleTestCase, TestCase, override_settings

from config.deployment import postgres_database
from .api import ApiError


@override_settings(ROOT_URLCONF="config.legacy_urls")
class DatabaseConfigurationTests(SimpleTestCase):
    def test_cloud_configuration_requires_credentials_and_verified_tls(self):
        with self.assertRaises(ImproperlyConfigured):
            postgres_database({})
        configuration = postgres_database({
            "PORTAL_DATABASE_HOST": "database.invalid", "PORTAL_DATABASE_USER": "portal",
            "PORTAL_DATABASE_PASSWORD": "test-only-password", "DATABASE_SSL_ROOT_CERT": "/cert/test.crt",
        })
        self.assertEqual(configuration["OPTIONS"]["sslmode"], "verify-full")
        self.assertEqual(configuration["OPTIONS"]["options"], "-c search_path=portal_private")
        self.assertEqual(configuration["ENGINE"], "django.db.backends.postgresql")


@override_settings(HOSTED_DEMO=True, REGISTRATION_ENABLED=False)
@override_settings(ROOT_URLCONF="config.legacy_urls")
class HostedAccessTests(TestCase):
    def test_public_home_and_login_do_not_request_browser_credentials(self):
        for path in ("/", "/ingresar/"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("WWW-Authenticate", response.headers)
            self.assertIn("no-store", response.headers["Cache-Control"])

    def test_panel_still_requires_individual_account_login(self):
        response = self.client.get("/panel/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/ingresar/")

    def test_basic_header_does_not_grant_account_permissions(self):
        response = self.client.get("/panel/", HTTP_AUTHORIZATION="Basic cmV2aXNpb246dW51c2Vk")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/ingresar/")

    def test_public_registration_remains_disabled(self):
        response = self.client.post("/cuenta/crear/", {})
        self.assertEqual(response.status_code, 403)

    def test_login_retains_browser_security_headers(self):
        response = self.client.get("/ingresar/")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])

    @patch("portal.views.request_api", return_value={"status": "ok"})
    def test_health_check_is_public_and_has_no_sensitive_details(self, api):
        response = self.client.get("/salud/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        api.assert_called_once_with("/health", timeout=2)

    @patch("portal.views.request_api", side_effect=ApiError(503, "internal-sensitive-detail"))
    def test_health_check_reports_api_failure_without_exposing_details(self, api):
        response = self.client.get("/salud/")
        self.assertEqual(response.status_code, 503)
        self.assertNotContains(response, "internal-sensitive-detail", status_code=503)

    @patch("portal.views.connection.cursor", side_effect=DatabaseError("internal-database-detail"))
    def test_health_check_reports_database_failure_without_exposing_details(self, cursor):
        response = self.client.get("/salud/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})

    @override_settings(SECURE_SSL_REDIRECT=True, SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"))
    def test_render_https_proxy_does_not_create_a_redirect_loop(self):
        response = self.client.get("/ingresar/", HTTP_X_FORWARDED_PROTO="https")
        self.assertEqual(response.status_code, 200)

    @override_settings(SECURE_SSL_REDIRECT=True)
    @patch("portal.views.request_api", return_value={"status": "ok"})
    def test_internal_http_health_probe_is_not_redirected(self, api):
        self.assertEqual(self.client.get("/salud/").status_code, 200)
