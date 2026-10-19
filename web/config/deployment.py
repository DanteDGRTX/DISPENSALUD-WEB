from django.core.exceptions import ImproperlyConfigured


def required(environment, name):
    value = environment.get(name, "")
    if not value.strip():
        raise ImproperlyConfigured(f"Falta configurar {name} para la demo alojada.")
    return value


def postgres_database(environment):
    return {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": required(environment, "PORTAL_DATABASE_HOST"),
        "PORT": environment.get("PORTAL_DATABASE_PORT", "5432"),
        "NAME": environment.get("PORTAL_DATABASE_NAME", "postgres"),
        "USER": required(environment, "PORTAL_DATABASE_USER"),
        "PASSWORD": required(environment, "PORTAL_DATABASE_PASSWORD"),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "sslmode": "verify-full",
            "sslrootcert": required(environment, "DATABASE_SSL_ROOT_CERT"),
            "connect_timeout": 5,
            "options": "-c search_path=portal_private",
        },
    }
