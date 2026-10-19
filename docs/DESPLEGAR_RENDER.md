# Demo restringida en Render

## Estado y límites

El repositorio privado ya aparece en Render. Esta guía prepara el despliegue, no acredita que esté publicado ni probado allí. Faltan credenciales PostgreSQL, certificado y una ejecución real del contenedor. No usar datos reales.

Para evitar crear dos servicios de pago, esta primera demo usa UN servicio Docker con Django/Gunicorn como entrada pública y Spring Boot en `127.0.0.1:8080`, accesible sólo dentro del contenedor. Un supervisor pequeño espera a la API antes de iniciar Gunicorn y detiene ambos procesos si uno falla. Al recibir SIGTERM, cierra los procesos hijos.

La base externa conserva el negocio en `dispensalud_private` y las sesiones Django en `portal_private`. No hay H2 ni SQLite de respaldo en este modo: si falta configuración o no hay conexión, el arranque falla. El disco del contenedor se considera desechable. Los datos locales del usuario NO se copian a la imagen ni se importan automáticamente.

Free puede suspenderse por inactividad y 512 MB es un presupuesto ajustado para ambos procesos. Se limita el heap Java a 192 MB y Gunicorn a un worker con dos threads. Falta comprobar el consumo y el arranque real; no se garantiza que ese plan baste. No se cambiará a un plan de pago automáticamente. Esta arquitectura de demo no sostiene una garantía de disponibilidad ni el control de un dispensador real.

## Antes de pulsar Deploy

1. Subir los archivos de esta preparación al repositorio privado, con autorización del propietario.
2. Preparar ambos esquemas privados en Supabase. La reserva del portal está en `api/deploy/supabase_portal_bootstrap.sql`. No exponerlos por la Data API. Las tablas se crean con Flyway y `manage.py migrate`, no copiando a mano sus migraciones al editor SQL.
3. Obtener la conexión adecuada desde Connect de Supabase: para redes sólo IPv4, revisar Session pooler; no usar el transaction pooler de forma intercambiable. Obtener el certificado de CA desde Database Settings y añadirlo en Render como Secret File llamado `supabase-ca.crt`, disponible en `/etc/secrets/supabase-ca.crt`.
4. Configurar credenciales de base como variables secretas, nunca en el repositorio ni por chat. Separar usuarios de negocio y portal y distinguir permisos de migración de permisos de ejecución antes de una publicación abierta. El arranque actual ejecuta las migraciones, por lo que sus roles requieren permisos de migración sobre SUS esquemas. Esa combinación es transitoria para una demo privada, no una configuración final de mínimos privilegios.
5. Ejecutar `scripts/New-RenderSecrets.ps1` una sola vez para generar `data/render.env`, ignorado por Git y Docker. Importar esos valores en Environment de Render sin copiarlos al chat. No modificar una clave ya utilizada sin planear su rotación. El propietario debe guardar los secretos fuera de esta laptop también.

## Campos del formulario que ya está abierto

| Campo | Valor |
|---|---|
| Source Code | `luisgustavosalcedo53-sys/dispensalud-proyect` |
| Name | `dispensalud-proyect`, si sigue disponible |
| Language | **Docker**, no Node ni Python |
| Branch | `main` |
| Root Directory | Vacío: el contexto es la raíz del repositorio |
| Dockerfile Path | `./Dockerfile` |
| Docker Command | Vacío: usar el CMD de la imagen |
| Compute | **Free**, comprobar que indique $0/mes antes de confirmar |
| Health Check Path | `/salud/` |
| Auto-Deploy | Desactivado al preparar y revisar esta primera demo |

No usar `yarn`, `yarn start`, `runserver` ni copiar comandos locales PowerShell al formulario. Docker reemplaza los comandos de build/start por el Dockerfile y su CMD.

## Variables y archivo secreto

Además de `data/render.env`, configurar:

| Variable | Contenido |
|---|---|
| `DATABASE_JDBC_URL` | `jdbc:postgresql://HOST:5432/postgres?sslmode=verify-full&sslrootcert=/etc/secrets/supabase-ca.crt` con el host real obtenido del panel; SIN contraseña dentro de la URL |
| `DATABASE_USER` | Usuario de la API; el nombre del pooler puede incluir el identificador del proyecto |
| `DATABASE_PASSWORD` | Contraseña de ese usuario, sólo en Environment |
| `DATABASE_SSL_ROOT_CERT` | `/etc/secrets/supabase-ca.crt` |
| `PORTAL_DATABASE_HOST` | Host real de la conexión de sesiones PostgreSQL |
| `PORTAL_DATABASE_PORT` | `5432` para la conexión de sesión seleccionada |
| `PORTAL_DATABASE_NAME` | `postgres` salvo que se configure otra base |
| `PORTAL_DATABASE_USER` | Usuario del esquema de sesiones del portal |
| `PORTAL_DATABASE_PASSWORD` | Su contraseña, sólo en Environment |

Render suministra `PORT` y `RENDER_EXTERNAL_HOSTNAME`; no inventar el dominio antes de que exista el servicio. El hostname exacto es el único host permitido en esta demo. Django reconoce HTTPS mediante el proxy de Render; esta confianza no debe copiarse a un servidor expuesto directamente sin un proxy que sanee las cabeceras. No añadir `*` a ALLOWED_HOSTS. Antes de publicar, verificar que peticiones externas no puedan falsificar el protocolo mediante cabeceras reenviadas.

El arranque comprueba la configuración, ejecuta las migraciones y activa explícitamente `cloud,demo`. El seed crea únicamente cuentas y un horario ficticios si la tabla de cuentas está vacía. Los usuarios son `cuidador.demo` y `usuario.demo`; la contraseña es `DISPENSALUD_DEMO_PASSWORD`, NO la contraseña de esta laptop. No hay registro público ni recuperación todavía. En una base con cuentas existentes, el seed no las modifica ni cambia sus contraseñas.

## Acceso y seguridad de esta demo

La URL está protegida primero por HTTP Basic con `DEMO_GATE_USER` y `DEMO_GATE_PASSWORD`; luego cada persona debe ingresar a su cuenta de DispenSalud. La contraseña del filtro se comparte sólo con revisores autorizados y puede rotarse. No equivale a invitaciones individuales, MFA, protección perimetral contra fuerza bruta ni autorización para datos clínicos reales. No compartirla en una presentación pública ni en GitHub.

`/salud/` es la excepción pública: responde sólo `ok` o `unavailable`, comprueba base y API y no expone usuarios, host, secretos o trazas. Los archivos estáticos públicos no contienen datos personales ni credenciales. Las páginas del portal llevan `no-store`. HSTS inicial de una hora, sin subdominios ni preload, es una decisión conservadora hasta verificar el dominio; `check --deploy` puede advertir esas dos opciones. Revisar las advertencias, no silenciarlas globalmente.

## Verificación y publicación

- `mvn package` en `api`: compila y ejecuta las pruebas de integración.
- `web/.venv/Scripts/python.exe manage.py test` desde `web` en Windows.
- `python -m unittest discover -s deploy` desde la raíz: pruebas del supervisor.
- Donde haya Docker: `docker build -t dispensalud-demo .`. Todavía no se puede afirmar que la imagen funcione sólo porque pasan pruebas Python/Java.
- Tras configurar secretos y aprobar la publicación: revisar el despliegue, `GET /salud/`, HTTPS, archivos estáticos, doble ingreso, permisos entre cuentas, escritura/lectura persistente y reinicio. Medir memoria antes de ampliar acceso.
- Si falla el build o el arranque, no cambiar a pago sin diagnóstico y autorización. Conservar logs sin contraseñas ni tokens.

La autorización para subir código NO implica autorización para contratar recursos ni publicar automáticamente. Este paso no completa registro, recuperación, consentimiento, invitaciones ni protección por origen: siguen pendientes antes de una demo abierta.

Referencias consultadas: https://render.com/docs/docker , https://render.com/docs/deploy-django , https://render.com/docs/health-checks , https://supabase.com/docs/guides/database/connecting-to-postgres
