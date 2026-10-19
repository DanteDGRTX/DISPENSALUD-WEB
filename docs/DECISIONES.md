# Requisitos y decisiones iniciales

## Roles y experiencia

### Cuidador

- Tiene una cuenta propia y acceso sólo a las personas que están vinculadas y autorizadas.
- Puede configurar medicamentos y horarios, asociar el dispensador, revisar eventos y corregir datos con un registro de auditoría.
- La interfaz web es el panel de gestión; Android puede ofrecerle una vista de cuidador si se confirma necesaria.

### Persona adulta mayor

- Tiene una cuenta separada, vinculada por autorización a su cuidador.
- La pantalla principal responde primero: “¿Qué me corresponde ahora?”. Usa pocas opciones, letra grande, alto contraste, frases cortas, iconos acompañados de texto y botones fáciles de tocar.
- No edita tratamientos ni tiene que navegar formularios.
- “Aviso mostrado”, “dosis dispensada”, “dosis retirada” y “persona indica que la tomó” son eventos distintos. La aplicación nunca convierte uno en prueba de otro.

La accesibilidad se validará con personas usuarias antes de fijar el diseño final; edad por sí sola no determina visión, audición, destreza o familiaridad tecnológica.

## Arquitectura

```text
Web Django + Bootstrap ──┐
                        ├── HTTPS/JSON ── Spring Boot API ── PostgreSQL en Supabase (pendiente)
Android Kotlin ──────────┘                           │
                                                    └── ESP32, fase posterior
```

- API REST versionada bajo `/api/v1`; las reglas de negocio y autorización se aplican en el servidor.
- Django sirve la web, los formularios y las sesiones técnicas; consulta Spring Boot desde el servidor. Las reglas y tablas de medicamentos y horarios tienen un único dueño: la API Spring Boot.
- El primer incremento local usa H2 en disco para negocio y SQLite para las sesiones técnicas del portal. La conexión externa a Supabase se prepara con un perfil separado y todavía debe validarse.
- PostgreSQL en Supabase es la base externa en nube recomendada para el proyecto: relacional, administrada y compatible con Spring Boot. La cadena de conexión se guarda como secreto del servidor o en `.env` local ignorado por Git.
- Se separan proyectos/credenciales de desarrollo y producción. Los clientes nunca reciben claves `service_role` ni la contraseña de PostgreSQL.
- Las tablas se gestionan con migraciones versionadas; no se modifica el esquema manualmente en producción.
- Los datos de desarrollo son sintéticos. Antes de usar datos reales se revisarán privacidad, retención, respaldos, control de acceso y obligaciones aplicables.

## Modelo funcional inicial

- `Account`: identidad y autenticación.
- `CareRelationship`: vínculo autorizado entre cuidador y persona atendida, con estado y permisos.
- `Medication`: nombre, presentación e instrucciones ingresadas por el cuidador. No genera recomendaciones médicas.
- `Schedule`: días, hora local, periodo de vigencia, zona horaria y casilla del dispensador.
- `DoseOccurrence`: una ocurrencia concreta con estado pendiente, en proceso, dispensada, retirada, reportada como tomada, omitida o error.
- `Device`: identidad del ESP32, vínculo con una persona atendida y versión de configuración.
- `DeviceEvent`: evento firmado/identificado de dispositivo, con hora del dispositivo y hora de recepción del servidor.
- `AuditEvent`: actor, operación, objeto y hora para cambios relevantes.

Los nombres son un modelo inicial; se ajustarán antes de generar migraciones.

## API inicial y rutas posteriores

- `POST /api/v1/auth/sessions`: inicio de sesión.
- `GET /api/v1/me`: cuenta y permisos disponibles.
- `GET|POST /api/v1/people/{personId}/medications`: listar y crear medicamentos autorizados.
- `GET|POST /api/v1/people/{personId}/schedules`: consultar y programar horarios.
- `GET /api/v1/people/{personId}/today`: vista diaria simplificada.
- Pendiente: `GET /api/v1/devices/{deviceId}/schedule-snapshot`, descarga de programación vigente para el ESP32.
- Pendiente: `POST /api/v1/devices/{deviceId}/events`, sincronización de eventos pendientes; aceptará identificadores idempotentes para no duplicarlos.

Cada ruta requiere autenticación y comprueba el vínculo con la persona atendida. El firmware tendrá credenciales de dispositivo propias, separadas de las cuentas humanas.

## Operación offline del ESP32

1. Cuando hay conexión, el dispositivo obtiene un plan versionado y de validez acotada para las próximas dosis, con zona horaria y una firma/validación de integridad.
2. Sin Internet, ejecuta sólo ocurrencias incluidas en esa copia vigente y con reloj confiable. No recibe cambios nuevos del cuidador hasta resincronizar.
3. Antes de accionar, guarda de forma persistente el identificador y estado de la ocurrencia. Los estados inciertos tras reinicio no se dispensan automáticamente otra vez.
4. Guarda los eventos localmente y los sube al reconectarse. La API deduplica por identificador único.
5. Si el plan vence, el reloj no es confiable o el estado mecánico es incierto, bloquea la dispensación automática y avisa cuando pueda comunicarlo.
6. La interfaz del cuidador muestra conexión y última sincronización. El tiempo máximo permitido sin conexión sigue pendiente de definición y pruebas.

El dispositivo puede informar que accionó el mecanismo o que un sensor detectó una caída/retiro. Ninguno de esos eventos demuestra ingestión. La mecánica debe tener sensores y pruebas específicas antes de afirmar que una pastilla salió correctamente.

## Herramientas

- VS Code: documentación, web, API y firmware.
- Android Studio: app Kotlin, emulador y depuración Android.
- Git/GitHub: historial de cambios y respaldo remoto. La carpeta local puede desarrollarse sin conectar la cuenta; el repositorio remoto se crea sólo al confirmar la cuenta destino.
- Supabase: PostgreSQL gestionado. La app empieza en local con secretos fuera del repositorio; no requiere publicar nada todavía.
