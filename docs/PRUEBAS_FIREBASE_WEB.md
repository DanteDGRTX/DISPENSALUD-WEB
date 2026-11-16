# Validación ejecutada · 16 noviembre 2026

La validación posterior de la recuperación del diseño está en
[RECUPERACION_DISENO_WEB.md](RECUPERACION_DISENO_WEB.md), incluyendo los resultados
actuales de Django, contrato, reglas Firebase y navegador. Las capturas y la barra
inferior descritas abajo corresponden a la primera presentación Firebase y quedan
como historial; la versión actual usa el diseño original y menú móvil desplegable.

Solo local. El propietario eligió **dejar la prueba real pendiente**. No se usaron
credenciales reales, pacientes reales, correos reales ni escrituras de producción.

| Comprobación | Resultado final |
|---|---|
| Django `manage.py test portal` | **35 correctas**, cero fallos/errores |
| Node `npm test` | **10 correctas**, cero fallos |
| Auth + Firestore Emulator `npm run test:emulator` | **13 correctas**, cero fallos |
| Total automatizado | **58 pruebas correctas** |
| `npm run build`, sintaxis JS y `manage.py check` | Correctos |
| `collectstatic --noinput` con WhiteNoise | Correcto; 27 recursos, 16 procesados/comprimidos |
| HTTP local de los 27 estáticos fuente | Todos HTTP 200 |
| Configuración DEBUG=0, proxy HTTPS y estáticos WhiteNoise | Acceso, panel, salud, bundle, CSS y fuente HTTP 200 |
| `manage.py check --deploy` | Sin errores; dos advertencias deliberadas W005/W021: HSTS sin includeSubDomains/preload |
| `git diff --check` de fuentes | Sin errores; bundle SDK y copia literal de reglas excluidos de formato |
| Android `git status --short` antes/después | Limpio; sin cambios |

Las advertencias HSTS se conservan para evitar comprometer otros subdominios antes
de inventariar el servidor y comprobar TLS. El HSTS básico, HTTPS, cookies seguras,
CSRF, CSP y cabeceras del proxy sí están configurados para producción. No se ha
verificado el servidor AWS real ni sus certificados.

## Servicios y reglas

La suite usa solo `demo-dispensalud-web`, Auth `127.0.0.1:9098`, Firestore
`127.0.0.1:8089` y la copia de reglas Android. Cubre registro/verificación/correo de
recuperación local, ingreso y salida; mismo UID en dos clientes; rechazo de otro
UID y correo no verificado; revisiones y conflicto; tombstones y prohibición de
resurrección/borrado físico; generación idempotente; edición/desactivación de
agenda; identidad SHA-256 Android; registro manual, procedencia y no reversión;
padres, propietarios y agendas inválidas; alertas/perfil; listeners y cancelación;
rechazo de caché offline y recuperación; revocación durante una lectura en curso y el máximo de 24 horarios diarios
(168 dosis confirmadas en una transacción e idempotencia al repetir).

El contrato puro prueba epoch-day/epoch-ms, validación estricta, Lima, horizonte de
siete días, conservación de horarios/resultados, bajas explícitas, convergencia de
duplicados, progreso sin futuras y con denominador cero, y errores legibles.

SHA-256 idéntico de `D:\dispensalud-codex\firestore.rules` y
`web/tests/android.firestore.rules`:
`D847052A76327D28023975545FFAF00BC1E662C0730492571FE1E6A294D40FFC`.
Esto valida la copia local; no afirma qué reglas están publicadas en Firebase.

La primera pasada detectó dos expectativas de prueba incorrectas (mañanas en el
intervalo de 168 horas y validación local antes del rechazo de reglas). Se
corrigieron. Una prueba exploratoria mostró que `disableNetwork` no garantiza
bloquear RPC de transacciones cuando el servidor sigue físicamente accesible;
se acotó a lo que sí verifica: lecturas exclusivamente del servidor, rechazo de
caché y recuperación. No se presenta como ensayo de desconexión física de escritura.

La preparación de estáticos detectó un sourcemap Bootstrap ausente. Se retiró solo
esa referencia de desarrollo, conservando licencia y CSS. Se usa WhiteNoise con
compresión sin exigir manifiesto de hashes; recopilar estáticos ya no falla.

## Navegador

En navegador integrado se recorrieron las pantallas con cuentas y pacientes
**FICTICIO**, exclusivamente en el emulador del puerto web 8001:

- Contraseña de confirmación distinta: error visible, sin crear la cuenta.
- Registro Usuario/Cuidador, verificación por enlace local y comprobación
  actualizada; preferencia Cuidador conservada en el perfil remoto.
- Alta de paciente y tratamiento desde formularios; escritura confirmada y plan
  de siete días. Sin porcentajes fabricados al comenzar sin dosis vencidas.
- Registro manual de una toma ya vencida: se mostró LATE, procedencia manual,
  fecha/hora y progreso 1/1; no se declaró ingestión verificada.
- Recarga de página restauró sesión y datos confirmados.
- Historial con paciente/fechas/estado, conservando el denominador de métricas.
- Edición concurrente desde un segundo cliente del mismo UID: el borrador se
  conservó, apareció la versión remota y solo se guardó tras elegir expresamente
  conservar el borrador y confirmar otra vez. Detalle confirmó el resultado.
- Perfil y cierre; otra cuenta verificada empezó sin pacientes/tratamientos ni
  información del usuario anterior.
- Reglas del emulador temporalmente cerradas: la carga mostró rechazo de permisos
  y reintento, sin aparentar éxito vacío. Se restauró la copia original local.
- Se detuvieron los emuladores para simular caída: al restaurar la sesión apareció
  “No se pudo conectar. Revisa tu conexión a Internet”, sin abrir datos privados.
- Desktop **1440×1000**, tablet **768×1024** y móvil **390×844**. Se inspeccionaron
  acceso, panel, historial y diálogos; fuentes/imágenes cargaron. Las mediciones
  de ancho de documento no excedieron el viewport. La navegación móvil quedó en
  una barra inferior de dos filas, sin desplazamiento horizontal global.
- La portada conservada se abrió en el puerto 8000; producto, logos, navegación
  y alcance actualizado visibles. Sus imágenes lazy se verificaron además por HTTP.
- Acceso final del proyecto Firebase real en `http://localhost:8000/ingresar/`,
  sin iniciar sesión ni crear cuentas reales. Capturas en `previews/firebase-login-desktop.jpg`
  y `previews/firebase-login-mobile.jpg`. El navegador comprime las capturas JPEG;
  la comprobación funcional se apoya también en DOM y respuestas HTTP.

Los emuladores y el servidor temporal 8001 se cerraron al terminar. La web 8000
reemplaza la copia local que ya estaba ejecutándose; Spring Boot existente no se
modificó ni se arrancó como dependencia nueva.

## Pendientes reales

No se han ejecutado con esta web las pruebas de una cuenta Android existente,
intercambio web↔Android, aislamiento entre cuentas reales ni correos reales. Son
pendientes explícitos del propietario, junto con revisar API key, dominios,
plantillas y reglas publicadas. Ver el recorrido en FIREBASE_WEB.md.
Los tests de dos clientes web no se presentan como ejecución del APK Android.

No se probaron hardware, ingestión, soporte offline de escritura, despliegue
AWS, DNS o renovación real. No se modificaron Android ni sus reglas publicadas.
