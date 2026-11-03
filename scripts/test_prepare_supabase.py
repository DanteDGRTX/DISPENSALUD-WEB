from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

import prepare_supabase


class PreparationTests(unittest.TestCase):
    def test_authentication_diagnostic_does_not_repeat_raw_error_or_password(self):
        error = prepare_supabase.psycopg.OperationalError("password authentication failed: secret-do-not-print")
        result = prepare_supabase.safe_diagnostic(error)
        self.assertIn("AUTENTICACION", result)
        self.assertNotIn("secret-do-not-print", result)

    def test_tls_diagnostic_keeps_verification_required(self):
        error = prepare_supabase.psycopg.OperationalError("certificate verify failed: private-detail")
        result = prepare_supabase.safe_diagnostic(error)
        self.assertIn("TLS", result)
        self.assertIn("No desactives SSL", result)
        self.assertNotIn("private-detail", result)

    def test_permission_and_unknown_errors_do_not_reveal_exception_details(self):
        permission = prepare_supabase.psycopg.errors.InsufficientPrivilege("private-detail")
        self.assertIn("PERMISOS", prepare_supabase.safe_diagnostic(permission))
        self.assertNotIn("private-detail", prepare_supabase.safe_diagnostic(RuntimeError("private-detail")))

    def test_generated_environment_never_contains_admin_credentials(self):
        passwords = {account[0]: f"test-secret-{number}" for number, account in enumerate(prepare_supabase.ACCOUNTS)}
        text = prepare_supabase.environment_text(passwords)
        self.assertEqual(len(text.splitlines()), 4)
        self.assertNotIn("postgres.", text)
        self.assertIn("DATABASE_USER=dispensalud_api_demo.", text)
        self.assertIn("PORTAL_DATABASE_USER=dispensalud_portal_demo.", text)

    @patch("prepare_supabase.psycopg.connect")
    def test_connections_require_full_certificate_and_hostname_verification(self, connect):
        prepare_supabase.connect("example", "test-only", Path("ca.crt"))
        self.assertEqual(connect.call_args.kwargs["sslmode"], "verify-full")
        self.assertEqual(connect.call_args.kwargs["sslrootcert"], "ca.crt")
        self.assertEqual(connect.call_args.kwargs["port"], 5432)

    def test_existing_roles_are_not_changed(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = ("existing",)
        with self.assertRaisesRegex(RuntimeError, "Ya existe"):
            prepare_supabase.provision(connection, {})
        self.assertEqual(cursor.execute.call_count, 1)

    def test_missing_schema_cancels_before_role_creation(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [None, (False,)]
        with self.assertRaisesRegex(RuntimeError, "Falta un esquema"):
            prepare_supabase.provision(connection, {})
        self.assertEqual(cursor.execute.call_count, 2)

    @patch("prepare_supabase.connect")
    def test_cross_schema_access_fails_verification(self, connect):
        cursor = connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (prepare_supabase.ACCOUNTS[0][0], True, True, True)
        with self.assertRaisesRegex(RuntimeError, "permisos"):
            prepare_supabase.verify_accounts({prepare_supabase.ACCOUNTS[0][0]: "test-only"}, Path("ca.crt"))


if __name__ == "__main__":
    unittest.main()
