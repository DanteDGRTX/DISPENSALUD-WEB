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
```

La suite de emulador requiere Java 21+ y puertos 8089/9098 libres. Usa únicamente
el proyecto local `demo-dispensalud-web`. No crea cuentas ni envía correos reales.
Las reglas copiadas en `tests` son una referencia local, no una configuración de
publicación. No ejecutar `firebase deploy` para esta entrega.

[Contrato, funciones y límites](../docs/FIREBASE_WEB.md) ·
[Resultados de pruebas](../docs/PRUEBAS_FIREBASE_WEB.md) ·
[Preparar AWS sin desplegar](../docs/DESPLEGAR_AWS_FIREBASE.md).

El código de la demo antigua permanece para consulta y pruebas bajo un URLconf
histórico, fuera de las rutas activas. No se importan sus cuentas ni registros.
