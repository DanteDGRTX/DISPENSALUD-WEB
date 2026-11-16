# Compatibilidad declarada y compuertas pendientes

Objetivo confirmado por el propietario: Ubuntu 26.04 LTS y CPython 3.14.4.
La preparación se ejecutó en Windows/Python 3.13. No se ejecutó Ubuntu, Gunicorn,
Nginx ni systemd del servidor; no se midió RAM remota. No confundir ambas cosas.

| Distribución fijada | Requires-Python | Declaración 3.14 |
|---|---|---|
| Django 5.2.18 | >=3.10 | Sí, classifier; Django 5.2 añadió soporte desde 5.2.8 |
| asgiref 3.12.1 | >=3.10 | Sí, classifier |
| sqlparse 0.6.0 | >=3.10 | Sí, classifier |
| WhiteNoise 6.12.0 | >=3.10 | Sí, classifier y documentación |
| Gunicorn 26.2.0 | >=3.10 | El rango permite 3.14; NO aparece en classifier ni CI de este tag |
| tzdata 2026.5 | >=2 | Datos de zonas independientes del intérprete, wheel universal |
| Pillow 13.0.0 / PyJWT 2.15.1 | >=3.11 / >=3.9 | Metadatos y wheels fijados; verificar runtime real |
| cryptography 50.0.2 / cffi 2.1.1 / pycparser 3.12 | Según DEPENDENCY_AUDIT.json | Wheels Linux x86_64/aarch64 compatibles con CPython 3.14 |

Metadatos exactos y enlaces de cada distribución en `DEPENDENCY_AUDIT.json` y
`reproduce/pypi-metadata.json`. Se comprueban también METADATA de los wheels,
el rango 3.14.4, hashes y cierre transitivo con marcadores Linux/CPython 3.14.
No se asume que un classifier o un rango garanticen ejecución en ese servidor.

Se omiten psycopg/PostgreSQL y packaging: este Gunicorn no exige packaging en su
variante sync sin extras; solo lo declara para extras que no se instalan. tzdata
se conserva como fallback pequeño para America/Lima sin depender del tzdb del host.
No hay Node, Java, pip de pruebas, emuladores, gevent, Tornado, h2 o herramientas
de compilación dentro de las dependencias de producción.

Fuentes primarias consultadas:

- [Django 5.2 y Python](https://docs.djangoproject.com/en/5.2/releases/5.2/#python-compatibility).
- [Django 5.2.18 en PyPI](https://pypi.org/pypi/Django/5.2.18/json).
- [WhiteNoise](https://whitenoise.readthedocs.io/en/stable/).
- [Gunicorn 26.2.0 metadatos](https://pypi.org/pypi/gunicorn/26.2.0/json) y
  [matriz CI del tag](https://github.com/benoitc/gunicorn/blob/26.2.0/.github/workflows/tox.yml).
- [Gunicorn configuración](https://gunicorn.org/reference/settings/).
- [Nginx HTTPS](https://nginx.org/en/docs/http/configuring_https_servers.html).
- [Certbot webroot](https://eff-certbot.readthedocs.io/en/stable/using.html#webroot).

## Comprobado localmente

Build frontend en Windows, árbol Git limpio y assets iguales al commit. Fuentes
de runtime extraídas de Git sin cambios funcionales. collectstatic con gzip previo
al envío, check --deploy sin errores y validación WSGI real en Windows con DEBUG=0,
los tres hosts, proxy HTTPS, rechazo de host desconocido, redirección desde HTTP,
cabeceras/cookies configuradas, 13 rutas y todos los estáticos recopilados.
Los resultados concretos están en WINDOWS_VALIDATION.json.

Dos advertencias HSTS son intencionales: no includeSubDomains ni preload para no
extender la política a los hosts AgroSmart. HSTS del código: 3600 segundos, solo
por host. No se modifican autenticación ni permisos Firebase; CSP permite solo los
servicios Google usados y no autoriza puertos de emulador en modo producción.
El secreto efímero de validación vive solo en memoria del proceso de build y NO
se empaqueta. El ejemplo de variables no contiene una clave real.

## Pendiente antes de activar

1. Gunicorn 26.2.0 en Ubuntu/Python 3.14.4: check-config y arranque real; no se
   cambia de versión silenciosamente para ocultar la falta de declaración expresa.
2. Confirmar socket libre 8002, módulos Python, memoria disponible y disco reales.
   MemoryHigh 128 MiB / MemoryMax 192 MiB son límites por servicio, NO medidas de
   consumo. Medir MemoryCurrent/MemoryPeak y los otros servicios antes/después.
3. Inventariar DNS A/AAAA, certificados, bloques Nginx y cuatro hosts AgroSmart.
   La fase raíz/www exige rutas existentes reales y edición manual delimitada.
4. Certificado nuevo exclusivo de app por webroot, nginx -t del host, recargas y
   renovación de ese certificado aisladas de hooks/certificados existentes.
5. Dominios autorizados y referrers Firebase; prueba de cuenta y cruce Android.

No se ejecutó ninguna de estas compuertas remotas. Tampoco se hizo push, merge,
despliegue, cambio de DNS, actualización del sistema o modificación de servicios.
