# DispenSalud

Repositorio privado: https://github.com/luisgustavosalcedo53-sys/dispensalud-proyect · Rama principal: `main`.

Primer incremento ejecutable local: API Spring Boot y portal Django con Bootstrap. Incluye cuentas distintas para cuidador y adulto mayor, permisos por persona, medicamentos y horarios diarios con datos ficticios.

La segunda iteración añade diseño inspirado en la referencia Figma, edición de indicaciones, pausa/reactivación de horarios, historial, ayuda y vista previa de la experiencia del adulto mayor. Para revisarla, sigue [`docs/PROBAR_DEMO.md`](docs/PROBAR_DEMO.md).

## Estructura

- `api/`: API REST con Spring Boot; autentica cuentas, aplica permisos, coordina horarios y registra eventos.
- `web/`: portal Django con Bootstrap, vistas, formularios y sesiones web.
- `android/`: aplicación Kotlin con una experiencia accesible para la persona adulta mayor y vistas de cuidador según permisos.
- `firmware/`: firmware ESP32, se implementa después de definir y probar el mecanismo físico.
- `docs/`: requisitos, arquitectura y decisiones del proyecto.

La web se comunica con la API desde Django. Android consumirá esa misma API. Supabase alojará PostgreSQL cuando configuremos y validemos la conexión externa. En local usamos H2 en disco para los datos ficticios y SQLite sólo para las sesiones técnicas de Django. Ningún cliente tendrá credenciales administrativas de la base.

## Ejecutar en Windows

Requisitos: Java 17 o superior, Maven y Python 3.13. Desde esta carpeta inicia la API en una terminal PowerShell:

```powershell
.\scripts\Start-Api.ps1
```

El script crea dos cuentas ficticias con contraseña aleatoria, guardada en `data/acceso-local.json`. Ese archivo y las bases locales están excluidos de Git. La contraseña se usa al crear la base por primera vez; conserva ese archivo para volver a ingresar.

En otra terminal inicia Django:

```powershell
.\scripts\Start-Web.ps1
```

Abre http://127.0.0.1:8000 e ingresa como `cuidador.demo` o `usuario.demo` con la contraseña del archivo local. El cuidador puede agregar un medicamento y una hora diaria. La persona mayor ve sus horarios sin opciones para configurar el tratamiento. Para detener cada servicio usa Ctrl+C en su terminal.

## Comprobar

La interfaz integrada del equipo tiene portada en `/`, ingreso en `/ingresar/`, registro de evaluación en `/cuenta/crear/` y panel en `/panel/`. El registro se permite en desarrollo local y queda cerrado por defecto en cloud. No concede vínculos automáticamente. Leer `docs/INTEGRACION_INTERFAZ.md` y el informe consolidado antes de publicar este incremento.

```powershell
cd api
mvn test
cd ..\web
.\.venv\Scripts\python.exe manage.py test portal
```

## Fases

La preparación de una demo restringida en Render está en [`docs/DESPLEGAR_RENDER.md`](docs/DESPLEGAR_RENDER.md). El runtime de ese despliegue es Docker, no Node. No publicar hasta configurar secretos, PostgreSQL, certificado y comprobar la imagen y los permisos en el entorno real.

1. Requisitos y estructura del repositorio.
2. API, autenticación, permisos y persistencia.
3. Panel del cuidador y flujo sencillo del adulto mayor.
4. Sincronización y operación offline limitada del ESP32.
5. Pruebas con datos ficticios y preparación para datos reales con revisión de privacidad y seguridad.

Lee [`docs/ESTADO.md`](docs/ESTADO.md) para distinguir funciones implementadas de pendientes y [`docs/DECISIONES.md`](docs/DECISIONES.md) para los flujos de dosis y dispositivo. El incremento actual muestra programación; Android, notificaciones y dispensación física requieren las siguientes fases.
