# API

Servicio central implementado con Spring Boot. Aplica autenticación, autorización por cuidador/persona atendida y validación de medicamentos y horarios diarios.

Rutas bajo `/api/v1`: `GET /health`, `POST /auth/sessions`, `DELETE /auth/sessions/current`, `GET /me`, `GET /people`, `GET|POST /people/{personId}/medications`, `POST /people/{personId}/schedules` y `GET /people/{personId}/today`.

Las rutas protegidas reciben `Authorization: Bearer TOKEN`. El servidor comprueba vínculos en cada operación. Los tokens duran ocho horas y sólo sus hashes se guardan; las contraseñas usan BCrypt.

El perfil `local` usa H2 en disco y crea cuentas ficticias sólo en la primera ejecución. El perfil `cloud` requiere `DATABASE_JDBC_URL`, `DATABASE_USER` y `DATABASE_PASSWORD`, usa PostgreSQL y no crea usuarios demo. El alta de cuentas cloud sigue pendiente. Flyway administra el esquema y la auditoría se guarda en la misma transacción que cada creación.

La sincronización con dispositivos sigue pendiente. Ejecuta `mvn test` para comprobar los permisos, relaciones, vencimiento, revocación y validación.

La segunda migración incorpora pausa de horarios, solicitudes de ayuda e historial vinculado a cada persona. Rutas adicionales:

- `PUT /people/{personId}/medications/{medicationId}`: editar nombre e indicación.
- `GET /people/{personId}/schedules`: consultar horarios habilitados y pausados.
- `PATCH /people/{personId}/schedules/{scheduleId}`: cambiar `enabled` de forma idempotente.
- `GET /people/{personId}/history`: últimos 50 eventos de la persona autorizada.
- `GET|POST /people/{personId}/help-requests`: consultar o solicitar ayuda. Sólo la persona usuaria crea su solicitud; se deduplican las solicitudes abiertas.
- `PATCH /people/{personId}/help-requests/{requestId}`: el cuidador autorizado la marca como atendida.
