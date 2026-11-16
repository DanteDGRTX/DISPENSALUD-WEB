# Web Firebase: entrega local

Fecha: 16 de noviembre de 2026. Rama `feature/firebase-web`, creada desde `main`
con el árbol de trabajo limpio. No se hizo push, merge ni despliegue. Android se
consultó exclusivamente en lectura; no se modificaron su código ni reglas publicadas.

## Arquitectura

Django conserva portada, plantillas y estáticos. Las rutas privadas sirven una
carcasa pública sin datos personales; Firebase Auth decide el acceso en el navegador
y Firestore aplica sus reglas por UID. No hay endpoints que acepten un UID como
autorización, sesiones privilegiadas, Firebase Admin ni cuentas de servicio.
La API Spring Boot y Supabase no son necesarios para esta versión.

El código histórico permanece para consulta/pruebas en `config/legacy_urls.py` y
los antiguos servicios, formularios y plantillas. **No está enlazado por las rutas
normales y no tiene ruta `/demo/` habilitada**. No se importan cuentas ni datos.

SDK modular Firebase **13.3.0**, esbuild **0.28.2**, reglas-unit-testing **6.0.0** y
Firebase CLI **15.36.0**, fijados en `web/package.json` y `package-lock.json`.
El bundle solo incorpora App, Authentication y Firestore. No se inicia Analytics,
Storage, Functions, SMS, facturación ni servicios de pago. La configuración pública
está centralizada en `web/frontend/firebase-config.js`.

Referencias: [SDK modular](https://firebase.google.com/docs/web/setup),
[transacciones](https://firebase.google.com/docs/firestore/manage-data/transactions),
[caché en memoria](https://firebase.google.com/docs/firestore/manage-data/enable-offline),
[versiones SDK](https://firebase.google.com/support/release-notes/js).

## Funciones

- Correo/contraseña de Firebase: registro con nombre y confirmación, recuperación
  neutra, verificación/reenvío, recarga de usuario y token, restauración y salida.
  Los correos solo se solicitan mediante acciones de la persona.
- Preferencias `Usuario` / `Cuidador` compatibles con Android. El nombre se guarda
  como `displayName` de Auth. El perfil se confirma en Firestore después de verificar
  el correo; antes de ello solo se conserva la selección en sessionStorage por UID.
- Pacientes: búsqueda, alta, detalle y edición. Tratamientos: alta, edición,
  horarios, fechas, compartimento previsto y desactivación/reactivación.
- Panel: filtro por paciente, próxima dosis y progreso de datos reales. Historial:
  paciente, fechas, estado, resultados, pendientes vencidas y métricas.
- Confirmación manual de toma/omisión, hora local en Lima, procedencia y momento
  de registro. Una toma posterior se marca LATE sin margen clínico inventado.
- Alertas: listado, leídas/sin leer y marcado como leídas. No se fabrican alertas.
- Perfil, cierre y equipo con “Sin dispositivo vinculado”.
- Estados de carga, vacío, error, reintento, escritura pendiente y acuse servidor.
  Los permisos rechazados no se convierten en listas vacías.
- Presentación web original oscura/azul, tipografía y logotipo originales,
  dispensador e iconos de perfil/navegación, tamaños adaptables y formularios
  etiquetados. La fuente Inter y otros recursos copiados se conservan disponibles;
  no sustituyen la tipografía global. Ver [recuperación del diseño](RECUPERACION_DISENO_WEB.md).

## Contrato exacto y concurrencia

Fuente de verdad leída: `FIREBASE_AUTH.md`, `LOCAL_ACCOUNTS.md`,
`FIRESTORE_SYNC.md`, `INTEGRATED_VERSION.md`; `Models.kt`, `SyncCodec.kt`,
`FirestoreRestTransport.kt`, `SyncJournal.kt`, `DoseScheduleIdentity.kt`,
`DosePlanner.kt`, `RoomRepositories.kt`, perfiles y `firestore.rules` Android.
Sus cabeceras vigentes indican que el usuario confirmó luego la sincronización;
las notas de reglas pendientes más abajo son históricas. No se ha auditado la
configuración publicada actual ni repetido aún esa validación con la web.

Rutas: `users/{uid}/patients`, `treatments`, `doseEvents`, `alerts` y
`preferences/presentation`. Sobre: `ownerUid`, `id`, `schemaVersion=1`, `revision`,
`mutationId`, `deleted`, `updatedAt` de servidor y `body`. Las listas incluyen
tombstones internamente. No hay consultas globales de otras cuentas.

Tratamientos: `fechaInicio` y `fechaFin` son **epoch-day**, no timestamps.
Dosis/alertas: instantes **epoch-ms**, precisión milisegundo. Horarios `HH:mm`.
Zona **America/Lima**, UTC−05. UUID compatibles, rechazo de prefijo `demo-`.
Fotos siempre `null`: las URI de fotos de Android no se exportan.

Las transacciones comprueban revisión y mutación de la versión mostrada. Una
edición concurrente conserva el borrador y muestra la versión del servidor; solo
la decisión explícita de conservar el borrador permite rebasarlo. No se resucitan
bajas ni se sobrescribe un resultado manual con un pendiente.

La identidad SHA-256 reproduce `v1|tratamiento|paciente|scheduleRevision|inicio|fin|activo|horariosOrdenados`
y `dose-SHA256(v1|tratamiento|epochMs|planKey)`. Horizonte `[ahora, ahora+7 días)`.
La reconciliación se ejecuta al entrar, guardar o desactivar tratamientos; el botón
“Generar próximos 7 días” permite extender/reintentar durante la sesión.
Conserva IDs de horarios aún vigentes, resultados y pasado; cancela pendientes
generados futuros afectados, con `deleted=true` y `retiredByPlanKey`. Las bajas
explícitas no reaparecen. Duplicados de agendas convergen al menor ID, o al resultado
ya confirmado, como Android. `scheduleRevision` crece solo si cambia la agenda.
El tratamiento también se revisa como bloqueo de transacción web; esto incrementa
su `revision` de sincronización al generar/registrar, sin cambiar la agenda.

El registro manual revisa estado pendiente, padres vivos, ausencia de otro resultado
conocido, fecha/hora no futuras y revisión. Guarda `recordSource=MANUAL`, `recordedAt`,
estado y hora real coherentes. No demuestra ingestión, retiro ni accionamiento.

Métrica: `(TAKEN + LATE) / dosis con horario <= ahora`, por paciente y periodo.
El filtro de estado afecta la lista, no el denominador. Con cero dosis vencidas se
muestra “—”. No se inventan stock, batería, diagnósticos ni porcentajes.

## Sesión y conexión

Auth se restaura por sesión del navegador. Cada apertura de cuenta crea una app
Firebase/Firestore separada con caché **solo en memoria**, fijada al usuario. Se
cancelan listeners, se termina Firestore y se elimina esa app al salir/cambiar de
cuenta. Se vacían datos, formularios, filtros, selección y diálogos; respuestas
tardías comprueban vigencia. Solo se presentan lecturas confirmadas del servidor,
nunca una caché vacía como éxito. El backend Django no recibe contraseñas.

Esta versión exige conexión para editar. Usa transacciones, no una cola durable
offline. Un fallo conserva el formulario para revisión; no promete que la escritura
se guardó. Si se pierde el acuse tras un commit, actualiza para comprobar el estado
antes de volver a editar. Cerrar la pestaña no conserva borradores.

## Arranque

En PowerShell desde `D:\dispensalud-web`:

```powershell
.\scripts\Start-Web.ps1
```

Abre **http://localhost:8000/ingresar/**, con el dominio autorizado `localhost`.
No necesitas `Start-Api.ps1`. Si cambias dependencias: `cd web; npm ci`.
Si editas JS: `npm run build`; recarga el navegador. Django usa `--noreload`:
los cambios Python requieren reiniciarlo. El script prepara `.venv`, dependencias,
bundle y sesiones técnicas Django. No crea identidades Firebase ni datos de negocio.

Pruebas reproducibles desde `web`:

```powershell
.\.venv\Scripts\python.exe manage.py test portal
npm test
npm run test:emulator
npm run build
```

Emulator Suite requiere Node 22+ y Java 21+; aquí se ejecutó con Node 24.22.0 y Java
26.0.2.1. Proyecto **demo-dispensalud-web**, Auth 9098 y Firestore 8089, solo loopback.
`tests/android.firestore.rules` es una copia de referencia, no una orden de publicar.
Compara su SHA-256 con Android al actualizar el contrato. La suite solo escribe
fixtures identificados como FICTICIO y cuentas `@example.test` en emuladores.

Para QA manual aislada: inicia `npx firebase emulators:start --config firebase.test.json --project demo-dispensalud-web --only auth,firestore`;
en otra terminal configura `$env:DISPENSALUD_FIREBASE_EMULATORS='1'` antes de arrancar
Django en otro puerto. La página muestra aviso naranja y cambia al proyecto demo.
Ese modo está deshabilitado con `DJANGO_DEBUG=0`. Nunca uses el emulador para
introducir las credenciales reales. No hay importación automática a producción.

## Validación y pendientes

Resultados y recorrido final: [PRUEBAS_FIREBASE_WEB.md](PRUEBAS_FIREBASE_WEB.md).
El usuario eligió continuar con la entrega y dejar la prueba real pendiente.

Pendiente con intervención del propietario, usando cuentas existentes y registros
**ficticios** reconocibles: ingreso Android→web, descarga de pacientes/tratamientos,
edición web→Android y Android→web, dosis/resultados sin duplicados, cambio a otra
cuenta sin datos anteriores, verificación y recuperación reales, cierre/restauración.
No se crearon cuentas ni se enviaron correos reales automáticamente.

Configuración externa: comprobar restricciones de la API key para este cliente web
y APIs necesarias; correo/contraseña, plantillas de correo, dominios autorizados y
reglas compatibles con el contrato Android vigente. No abrir reglas para superar
errores. Revisar cuota Spark antes de aumentar volumen: se leen las colecciones
propias completas y se usan listeners; el horizonte admite hasta 24 horarios/día
por tratamiento. No hay paginación remota en esta primera versión.

Pendientes funcionales fuera del alcance: colaboración entre cuentas, dispositivo
físico, notificaciones push, fotos remotas y escritura offline. AWS/DNS/HTTPS se
preparan en [DESPLEGAR_AWS_FIREBASE.md](DESPLEGAR_AWS_FIREBASE.md), sin ejecutarlos.

## Archivos

- `web/frontend/`: configuración, contrato, repositorio y presentación.
- `web/package*.json`, `build.mjs`, `firebase.test.json`, `tests/`: build/pruebas.
- `web/portal/firebase_views.py`, `templates/portal/firebase.html`, estáticos
  `firebase/` y recursos con licencia: nuevas pantallas.
- `web/config/urls.py`, `legacy_urls.py`, `settings.py`, middleware: rutas, CSP,
  estáticos y configuración. Tests anteriores conservados bajo URLconf histórico.
- Portada/product_base/product.py: recursos actuales y afirmaciones corregidas.
- `scripts/Start-Web.ps1`, README, `.env.example`, `deploy/aws/` y estos informes.
