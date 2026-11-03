import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import start


class StartTests(unittest.TestCase):
    def test_missing_configuration_fails_before_starting_processes(self):
        with patch.dict(os.environ, {}, clear=True), patch("start.subprocess.Popen") as launch:
            with self.assertRaisesRegex(RuntimeError, "DJANGO_SECRET_KEY"):
                start.main()
            launch.assert_not_called()

    def test_conflicting_tls_options_and_credentials_in_url_are_rejected(self):
        for value in (
            "jdbc:postgresql://test.invalid/postgres?sslmode=verify-full&sslmode=disable&sslrootcert=/ca.crt",
            "jdbc:postgresql://test.invalid/postgres?sslmode=verify-full&sslrootcert=/wrong.crt",
            "jdbc:postgresql://user:password@test.invalid/postgres?sslmode=verify-full&sslrootcert=/ca.crt",
        ):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                start.validate_jdbc_url(value, Path("/ca.crt"))

    def environment(self, certificate):
        return {
            "DJANGO_SECRET_KEY": "test-only-key" * 5, "RENDER_EXTERNAL_HOSTNAME": "test.invalid",
            "DATABASE_JDBC_URL": f"jdbc:postgresql://test.invalid/postgres?sslmode=verify-full&sslrootcert={certificate}",
            "DATABASE_USER": "api", "DATABASE_PASSWORD": "test-only-db-password",
            "DATABASE_SSL_ROOT_CERT": str(certificate), "PORTAL_DATABASE_HOST": "test.invalid",
            "PORTAL_DATABASE_USER": "portal", "PORTAL_DATABASE_PASSWORD": "test-only-db-password",
            "DISPENSALUD_DEMO_PASSWORD": "test-only-demo-password",
        }

    def test_unverified_database_connection_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            certificate = Path(directory) / "ca.crt"
            certificate.write_text("test-only-certificate")
            environment = self.environment(certificate)
            environment["DATABASE_JDBC_URL"] = "jdbc:postgresql://test.invalid/postgres?sslmode=require"
            with patch.dict(os.environ, environment, clear=True), self.assertRaisesRegex(RuntimeError, "TLS"):
                start.main()

    def test_stopping_container_terminates_children(self):
        process = MagicMock()
        process.poll.return_value = None
        start.terminate([process])
        process.terminate.assert_called_once()
        process.wait.assert_called_once()

    def test_unresponsive_child_is_killed_after_shutdown_timeout(self):
        process = MagicMock()
        process.poll.return_value = None
        process.wait.side_effect = [start.subprocess.TimeoutExpired("test", 20), 0]
        start.terminate([process])
        process.kill.assert_called_once()

    def test_web_failure_stops_api_and_forces_container_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            certificate = Path(directory) / "ca.crt"
            certificate.write_text("test-only-certificate")
            api = MagicMock()
            api.poll.return_value = None
            web = MagicMock()
            web.poll.return_value = 1
            with patch.dict(os.environ, self.environment(certificate), clear=True), \
                    patch("start.signal.signal"), patch("start.subprocess.run") as run, \
                    patch("start.subprocess.Popen", side_effect=[api, web]) as launch, \
                    patch("start.urlopen") as health:
                health.return_value.__enter__.return_value.status = 200
                with self.assertRaisesRegex(RuntimeError, "componente"):
                    start.main()
                self.assertEqual(run.call_count, 2)
                self.assertEqual(launch.call_count, 2)
                api.terminate.assert_called_once()
                self.assertEqual(os.environ["API_BIND_ADDRESS"], "127.0.0.1")
                self.assertEqual(os.environ["DJANGO_DEBUG"], "0")


if __name__ == "__main__":
    unittest.main()
