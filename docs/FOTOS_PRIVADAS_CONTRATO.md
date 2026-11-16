# Fotos privadas v1 — contrato previo a los clientes

Identidad: Firebase ID token mediante `Authorization: Bearer …`, correo verificado,
proyecto configurado. Django verifica firma RS256, issuer, audience, caducidad y
cuenta vigente. Nunca acepta UID del cliente como autorización. Se consulta
Firestore REST con el mismo token para comprobar que el paciente pertenece al UID
y no está dado de baja; no se utilizan credenciales Admin ni cuentas de servicio.
Solo desarrollo explícito admite Auth/Firestore Emulator de proyecto demo.

## Diagnóstico inicial (ambos repositorios limpios)

Web base `25247ab`; Android base `f719117`. Perfil de cuenta: AuthUser Android
contiene uid/nombre/correo/verificación, sin foto; las ilustraciones de perfil son
recursos estáticos. Pacientes: Room conserva `Patient.foto` como URI local,
OpenDocument conserva el permiso y el avatar solo decodifica content/file/resource.
SyncCodec exporta siempre `foto:null` y conserva la URI local al importar. Web y
reglas v1 también exigen null; la web solo dibuja iniciales y no sube archivos.
No existe una referencia remota ni una subida que el CSS pudiera recuperar.
CSP actual no admite blob; se habilita exclusivamente para previsualización y
lectura autenticada web, nunca como referencia sincronizada.

## Referencias y API

Origen HTTPS configurado, inicialmente app.dispensalud.site para validar y www
para la dirección definitiva. Referencia opaca `private-photo:v1:<UUID hex 32>`.
No es una URL pública, una URI local, base64 ni un token. El índice de Django es
la fuente compartida entre clientes; Firestore mantiene `patients.body.foto:null`
y `preferences.presentation.profile` sin cambios. **No necesita cambiar reglas
Firestore**, ni publicadas ni locales. Las fotos de perfil y paciente son sujetos
distintos: `profile` y `patient:<id>`.

- `GET /api/photos/v1/`: índice de referencias de la cuenta autenticada.
- `GET /api/photos/v1/profile/`: metadatos de la foto de cuenta.
- `GET /api/photos/v1/patients/<id>/`: metadatos del paciente, tras autorizarlo.
- `PUT` sobre uno de esos dos sujetos: cuerpo binario JPEG/PNG/WebP, Content-Type
  coherente y Content-Length conocido. Headers `If-Match: <etag>` e
  `Idempotency-Key: <UUID>` obligatorios. No se reciben URLs para descargar.
- `DELETE` sobre el sujeto: `If-Match` obligatorio, elimina la versión compartida.
- `GET /api/photos/v1/files/<photoId>/`: JPEG normalizado, autenticación y
  autorización en cada lectura. Referencias sustituidas o de otra cuenta: 404.

Metadatos: `{subject,state,reference,photoId,etag}`. `state` es `empty` (sin subida),
`ready` o `deleted`. ETag inicial `none`; las mutaciones crean un identificador
servidor nuevo. Un conflicto devuelve 409 y exige recargar, sin sobreescribir la
foto de otro dispositivo. La misma clave idempotente y contenido recupera la
respuesta de la subida confirmada; reutilizarla con otro contenido da conflicto.

Errores JSON controlados `{error:{code,message}}`: 401 token inválido/caducado,
403 correo sin verificar/origen no permitido, 404 sujeto/archivo no autorizado,
409 conflicto, 413 tamaño, 415 formato, 422 imagen inválida/dimensiones,
428 precondición ausente, 507 cuota y 503 fallo de conexión/almacenamiento.
Sin tokens en URLs, logs ni errores; no se autoriza mediante cookies. No se
habilita CORS general. Respuestas privadas no-store, Vary Authorization, nosniff.

## Archivos, recursos y persistencia

Entrada máxima 2 MiB; JPEG/PNG/WebP de una sola imagen, firma y decodificación
reales. Máximo 4096 por dimensión y 4.194.304 píxeles antes de decodificar.
Se rechazan SVG/GIF/animaciones/HEIC y contenido corrupto. Orientación EXIF
aplicada; metadatos eliminados; JPEG hasta 512×512 conservando proporción,
máximo 128 KiB, transparencia sobre fondo azul oscuro. No se almacenan originales.

Todo bajo `DJANGO_DATA_DIR/private-photos`: SQLite de metadatos y carpetas por
SHA-256 del UID, archivos con UUID generados por servidor y permisos privados.
En producción queda bajo `/srv/dispensalud-web/shared`, fuera de releases/static.
Nginx nunca publica ese directorio. Cuota predeterminada 8 MiB/UID, 64 fotos/UID,
128 MiB global, configurable hacia límites revisados. Bloqueo transaccional al
comprobar cuotas y sustituir; la versión anterior se borra después de confirmar
la nueva. Recolección controlada de huérfanos con antigüedad, dry-run por defecto.
No se borran archivos locales Android antiguos, ni desde el servidor ni al migrar.
El índice también limita metadatos a 256 sujetos/UID y 4096 globales para acotar
las bajas. DELETE permite liberar la foto de un paciente propio dado de baja,
pero no leerla ni sustituirla. No se aceptan pacientes ajenos o inexistentes.

## Clientes y compatibilidad

Web: selección y previsualización blob temporal, envío explícito, estado/error/
reintento; lectura fetch autenticada y ObjectURL revocable. Iniciales como fallback.
La caché es de la sesión/UID y se aborta/revoca al cambiar de cuenta.

Android: conserva URI y permiso local; subir es una acción explícita. Los archivos
locales anteriores siguen disponibles para ofrecer subirlos. La referencia remota
vive en el índice común y caché privada por UID/photoId, separada de Room.foto.
Una eliminación remota muestra iniciales y conserva la copia local para subirla
otra vez solo a petición. Cambio de cuenta no reutiliza caché ni solicitudes.

Validación exigida: cuenta A/B, token falso/expirado, propiedad de paciente,
contenido/tamaño/cuota, CAS/reintento, sustitución/eliminación, fallo de red,
persistencia/reinicio y recorrido bidireccional con imágenes ficticias. Emuladores
y mocks se documentan aparte de pruebas remotas reales. AWS permanece sin cambios.
