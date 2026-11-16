# Portal Dispensalud con Firebase

Django sirve la portada, las pantallas y los estáticos. El SDK modular Firebase
comparte Authentication y Firestore con Android. Los datos privados se autorizan
por UID y correo verificado; no existe una sesión de negocio Django ni endpoints
privilegiados. Spring Boot y Supabase no son necesarios para estas pantallas.

Desde la raíz en PowerShell:

```powershell
.\scripts\Start-Web.ps1
```

Abre http://localhost:8000/ingresar/. Requiere Python 3.13 y Node 22+.
El script prepara el entorno, instala dependencias y compila el cliente.
Después de cambiar dependencias, ejecuta `npm ci` dentro de `web`.
Para cambios JS usa `npm run build` y recarga. Reinicia Django tras cambios Python.

```powershell
cd web
.\.venv\Scripts\python.exe manage.py test portal
npm test
npm run test:emulator
npm run build
npm run test:browser
```

La suite de emulador requiere Java 21+ y puertos 8089/9098 libres. Usa únicamente
el proyecto local `demo-dispensalud-web`. No crea cuentas ni envía correos reales.
Las reglas copiadas en `tests` son una referencia local, no una configuración de
publicación. No ejecutar `firebase deploy` para esta entrega.

El diseño recuperado utiliza las plantillas originales con cabecera/pie compartidos.
`frontend/presentation.js` contiene la presentación; `main.js` conserva Firebase y
los eventos de los controles. El build genera `app.js` y `panel-web.css`: esta
última limita Bootstrap y los estilos originales del panel a `.web-workspace`,
sin alterar la portada ni el formulario de acceso. `app.css` adapta los controles
Firebase. La eliminación de `landing.css` es intencional; no debe volver a enlazarse.

Las pruebas de navegador usan Brave en Windows por defecto; para otro ejecutable
Chromium, configura `$env:DISPENSALUD_BROWSER = 'C:\ruta\chrome.exe'`.
`npm run test:browser` inicia/cierra su Django temporal en 8002 y los emuladores;
no modifica el servidor 8000 ni necesita cuentas reales. Requiere el entorno
`.venv` preparado y esos puertos libres.

Comparación opcional: `npm run test:visual`, con la web actual en 8000 y la
referencia ya servida en 8001. `DISPENSALUD_ORIGINAL` permite indicar la carpeta
de referencia; solo se leen sus plantillas. No arrancar servicios ni instalar
dependencias dentro de esa carpeta. Las capturas/informes van a
`previews/design-correction/` y `web/build/`, excluidos de Git.

Para revisar los ajustes finales del dispensador, las dos tarjetas de beneficios
y los iconos: `npm run test:visual:final`. Usa la web ya servida en 8000, sin
referencia original ni cuentas reales; verifica 320, 390, 768 y 1440 px. Guarda
capturas reales del acceso, beneficios y portada completa en
`previews/visual-final/`, excluido de Git. Detalles en
[AJUSTES_VISUALES_WEB.md](../docs/AJUSTES_VISUALES_WEB.md).

[Contrato, funciones y límites](../docs/FIREBASE_WEB.md) ·
[Resultados de pruebas](../docs/PRUEBAS_FIREBASE_WEB.md) ·
[Recuperación del diseño](../docs/RECUPERACION_DISENO_WEB.md) ·
[Preparar AWS sin desplegar](../docs/DESPLEGAR_AWS_FIREBASE.md).

El código de la demo antigua permanece para consulta y pruebas bajo un URLconf
histórico, fuera de las rutas activas. No se importan sus cuentas ni registros.
