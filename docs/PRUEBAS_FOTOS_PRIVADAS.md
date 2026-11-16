# Fotos privadas — preparación local

Contrato previo a clientes: `FOTOS_PRIVADAS_CONTRATO.md`. Fuentes web base
25247ab y Android base f719117 se inspeccionaron primero en lectura, ambas limpias.
Fotos de perfil no implementadas anteriormente; fotos de paciente locales en Room
se excluían deliberadamente de SyncCodec. No se encontraron subidas remotas.

Servidor/web: 44 pruebas Django (8 nuevas de fotos), 10 de contrato JS y recorrido
HTTP+navegador en emuladores, con PNG ficticio generado en build. Se comprueba
RS256 real con claves efímeras de prueba, audience/caducidad/verificación y
revocación; aislamiento por UID, propiedad paciente, MIME/contenido, dimensiones,
cuota, CAS, idempotencia, sustitución, eliminación y fallo de conexión.

El recorrido usa Auth/Firestore Emulator y Django 8003. El cliente HTTP representa
el contrato que usará Android, no ejecución del APK. El navegador muestra su
subida, sustituye la foto, reintenta sin perder selección tras quedar offline y
elimina. Se detiene y arranca Django con el mismo directorio privado y se conserva
la referencia y bytes. Otra cuenta recibe 404. Firestore mantiene foto:null.

Recorrido de regresión de diseño/cuentas con emuladores en `npm run test:browser`.
Pruebas de datos y reglas existentes no requieren modificaciones para fotos.

```powershell
cd web
.\.venv\Scripts\python.exe manage.py test portal
npm test
npm run build
npm run test:photos
npm run test:browser
```

La receta reproducible se guarda ahora en `deploy/release/prepare_release.py`.
Genera fuera del repositorio una release del commit exacto, con frontend compilado
Windows, imágenes privadas excluidas y wheels fijados para Linux/Python 3.14 en
x86_64/aarch64. Instrucciones nuevas preservan shared y los servicios AgroSmart.

Android se trabaja a continuación con commit propio. La ejecución cruzada del
APK y los artefactos finales se informarán por separado; este registro no acredita
producción. No se conectó a AWS, no se publicaron reglas ni se activó Storage/Blaze.
