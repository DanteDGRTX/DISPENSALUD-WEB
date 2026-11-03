import getpass
import os
from pathlib import Path
import secrets
import sys
import warnings

import psycopg
from psycopg import sql


PROJECT = "cgpdfmubokvmgiqpzalc"
HOST = "aws-0-us-east-1.pooler.supabase.com"
ACCOUNTS = (
    ("dispensalud_api_demo", "dispensalud_private", "portal_private", 8),
    ("dispensalud_portal_demo", "portal_private", "dispensalud_private", 6),
)


def safe_diagnostic(error):
    state = getattr(error, "sqlstate", None)
    if state == "28P01":
        return "AUTENTICACION: Supabase rechazó las credenciales. No cambies la contraseña todavía."
    if state == "42501":
        return "PERMISOS: la cuenta conectada no permite una de las operaciones solicitadas."
    if isinstance(error, psycopg.OperationalError):
        detail = str(error).lower()
        if any(marker in detail for marker in ("password authentication failed", "sasl authentication failed", "wrong password")):
            return "AUTENTICACION: Supabase rechazó las credenciales. No cambies la contraseña todavía."
        if "no password supplied" in detail:
            return "SIN_CONTRASENA: no llegó una contraseña a la conexión."
        if "certificate" in detail or "ssl error" in detail:
            return "TLS: no se pudo verificar el certificado o el nombre del servidor. No desactives SSL."
        if "tenant or user not found" in detail:
            return "USUARIO_POOLER: el servidor no reconoce el usuario o el proyecto de esta conexión."
        if "timeout" in detail or "timed out" in detail:
            return "RED: se agotó el tiempo de conexión."
        return "CONEXION: falló la conexión PostgreSQL."
    if isinstance(error, (PermissionError, FileExistsError)):
        return "ARCHIVO: no se pudo crear o renombrar el archivo local sin sobrescribir datos."
    if isinstance(error, getpass.GetPassWarning):
        return "TERMINAL: no hay entrada oculta disponible; se canceló antes de mostrar la contraseña."
    if isinstance(error, (KeyboardInterrupt, EOFError)):
        return "CANCELADO: la entrada de terminal se interrumpió."
    if isinstance(error, psycopg.Error):
        if state and len(state) == 5 and state.isalnum():
            return f"POSTGRESQL: código SQLSTATE {state}."
        return "POSTGRESQL: la base rechazó una operación."
    return "PREPARACION: falló una comprobación interna."


def connect(username, password, certificate):
    return psycopg.connect(
        host=HOST, port=5432, dbname="postgres", user=f"{username}.{PROJECT}",
        password=password, sslmode="verify-full", sslrootcert=str(certificate), connect_timeout=10,
    )


def provision(connection, passwords):
    with connection.cursor() as cursor:
        cursor.execute("SELECT rolname FROM pg_roles WHERE rolname = ANY(%s)",
            ([account[0] for account in ACCOUNTS],))
        if cursor.fetchone():
            raise RuntimeError("Ya existe uno de los usuarios. No se cambian contraseñas ni permisos existentes.")
        for username, own_schema, other_schema, limit in ACCOUNTS:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = %s)", (own_schema,))
            if not cursor.fetchone()[0]:
                raise RuntimeError("Falta un esquema privado. No se crean usuarios.")
        for username, own_schema, other_schema, limit in ACCOUNTS:
            cursor.execute(sql.SQL(
                "CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE "
                "NOINHERIT NOREPLICATION NOBYPASSRLS CONNECTION LIMIT {}"
            ).format(sql.Identifier(username), sql.Literal(passwords[username]), sql.Literal(limit)))
            cursor.execute(sql.SQL("GRANT CONNECT ON DATABASE postgres TO {}").format(sql.Identifier(username)))
            cursor.execute(sql.SQL("GRANT USAGE, CREATE ON SCHEMA {} TO {}")
                .format(sql.Identifier(own_schema), sql.Identifier(username)))
            cursor.execute(sql.SQL("ALTER ROLE {} IN DATABASE postgres SET search_path TO {}")
                .format(sql.Identifier(username), sql.Identifier(own_schema)))
            cursor.execute("SELECT has_schema_privilege(%s, %s, 'USAGE')", (username, other_schema))
            if cursor.fetchone()[0]:
                raise RuntimeError("Se detectó acceso entre esquemas. Se cancela la transacción.")


def environment_text(passwords):
    return "\n".join((
        f"DATABASE_USER={ACCOUNTS[0][0]}.{PROJECT}",
        f"DATABASE_PASSWORD={passwords[ACCOUNTS[0][0]]}",
        f"PORTAL_DATABASE_USER={ACCOUNTS[1][0]}.{PROJECT}",
        f"PORTAL_DATABASE_PASSWORD={passwords[ACCOUNTS[1][0]]}",
        "",
    ))


def verify_accounts(passwords, certificate):
    for username, own_schema, other_schema, limit in ACCOUNTS:
        with connect(username, passwords[username], certificate) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT current_user, has_schema_privilege(current_user, %s, 'USAGE'), "
                    "has_schema_privilege(current_user, %s, 'CREATE'), "
                    "has_schema_privilege(current_user, %s, 'USAGE')",
                    (own_schema, own_schema, other_schema),
                )
                if cursor.fetchone() != (username, True, True, False):
                    raise RuntimeError("La comprobación de permisos no coincide con lo previsto.")


def main():
    root = Path(__file__).resolve().parent.parent
    certificate = root / "data" / "supabase-ca.crt"
    destination = root / "data" / "render-database.env"
    pending = root / "data" / "render-database.pending"
    if destination.exists() or pending.exists():
        print("Ya existe un archivo de esta preparación. No se sobrescribe. Avísanos antes de repetirla.")
        return 1
    if not certificate.is_file():
        print("Falta data/supabase-ca.crt. No se puede verificar la conexión cifrada.")
        return 1
    if not sys.stdin.isatty():
        print("Ejecuta este asistente en una terminal interactiva de VS Code o PowerShell, no desde el chat.")
        return 1
    print("Destino: dispensalud-demo, en tu proyecto de Supabase.")
    print("Se crearán dos usuarios nuevos, uno para la API y otro para las sesiones del portal.")
    print("Cada uno podrá crear y migrar tablas sólo en su esquema privado; no será administrador.")
    print("Es una preparación de demo: separar migraciones de ejecución queda pendiente para producción.")
    print("No se cambia la contraseña de postgres, no se publica la web ni se contratan recursos.")
    if input("Escribe CREAR si autorizas estos dos usuarios: ").strip() != "CREAR":
        print("Cancelado sin cambios.")
        return 0
    warnings.simplefilter("error", getpass.GetPassWarning)
    phase = "leer contraseña oculta"
    try:
        admin_password = getpass.getpass("Contraseña de base de datos que guardaste en Supabase (oculta): ")
        if not admin_password:
            print("No se introdujo una contraseña. Cancelado.")
            return 1
        passwords = {account[0]: secrets.token_hex(24) for account in ACCOUNTS}
        phase = "autenticar la cuenta administradora"
        with connect("postgres", admin_password, certificate) as connection:
            phase = "crear usuarios y asignar permisos, dentro de una transacción"
            provision(connection, passwords)
            phase = "guardar las claves nuevas en el archivo pendiente"
            descriptor = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                output.write(environment_text(passwords))
                output.flush()
                os.fsync(output.fileno())
            phase = "confirmar la transacción de creación"
        admin_password = None
        phase = "probar la conexión y permisos de los dos usuarios nuevos"
        verify_accounts(passwords, certificate)
        phase = "renombrar el archivo verificado para importarlo en Render"
        pending.rename(destination)
        print("Usuarios creados y conexiones TLS/permisos comprobados.")
        print("Importa data/render-database.env en Environment Variables de Render.")
        print("Ese archivo contiene secretos de la aplicación: no lo pegues en el chat ni lo subas a Git.")
        print("La contraseña administradora no se guardó. Todavía NO pulses Deploy.")
        return 0
    except (Exception, KeyboardInterrupt) as error:
        print("No se completó la preparación. No se muestran contraseñas ni detalles sensibles del error.")
        print(f"Paso: {phase}.")
        print(safe_diagnostic(error))
        print("Si existe data/render-database.pending, consérvalo sin importarlo: puede requerir revisión.")
        print("No repitas el asistente ni cambies las contraseñas por tu cuenta; comunica este resultado.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
