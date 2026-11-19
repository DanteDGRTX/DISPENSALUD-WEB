# DispenSalud

## Integración para Desarrollo de Aplicaciones Web · 19 noviembre 2026

La rama de integración incorpora gestión de pacientes con Spring MVC/Thymeleaf,
capas y puertos/adaptadores, y un segundo servicio de supervisión por agentes
reactivos. Usa las cuentas y el contrato Firebase existentes. Arranque:
`./scripts/Start-Course.ps1` en Windows o `bash scripts/start-course.sh` en Linux.
Guía, evidencias de arquitectura y recorrido de exposición en
[SPRING_CURSO.md](docs/SPRING_CURSO.md). Esta integración todavía no está desplegada.


## Versión final Firebase y fotos privadas · 16 noviembre 2026

Web pública: **https://www.dispensalud.site**. Repositorio personal privado:
[DanteDGRTX/DISPENSALUD-WEB](https://github.com/DanteDGRTX/DISPENSALUD-WEB), rama
principal **`feature/firebase-web`**. Android:
[DanteDGRTX/DISPENSALUD-ANDROID](https://github.com/DanteDGRTX/DISPENSALUD-ANDROID).

La versión actual usa **Django + Firebase Authentication/Firestore**, con las mismas
cuentas y el contrato Android de `D:\dispensalud-codex`. No necesita iniciar Spring
Boot ni Supabase. No importa cuentas ni registros de la demo anterior.

Desde PowerShell: `.\scripts\Start-Web.ps1`. Abre http://localhost:8000.
Requiere Python 3.13 y Node.js 22 o superior. Las dependencias están fijadas.

Lee [web/README.md](web/README.md), [funciones y sincronización](docs/FIREBASE_WEB.md),
[contrato de fotos privadas](docs/FOTOS_PRIVADAS_CONTRATO.md) y
[publicación, pruebas y operación](docs/PUBLICACION_PRIVADA.md).

Incluye acceso/registro/verificación y recuperación Firebase, cuentas separadas
por UID, perfiles de presentación Usuario/Cuidador, pacientes, tratamientos,
horarios, historial/registro manual y alertas. Las fotos de perfil y paciente se
suben a Django por acción explícita y se leen con token Firebase y autorización;
se comparten con Android sin Firebase Storage ni base64 en Firestore. No se
simulan vinculación física, batería, stock o dispensación.

El usuario confirmó el 16/11/2026 que instaló la última versión de fotos en AWS
y probó manualmente Android ↔ web correctamente. La publicación en GitHub no
accede ni modifica AWS, Firebase, DNS, AgroSmart o la web desplegada. Las pruebas
automatizadas anteriores se ejecutaron localmente y se documentan por separado.

Diseño web original recuperado conservando Firebase, con cabecera/pie compartidos,
dispensador e iconos necesarios. Guía de cambios, reproducción y comprobaciones en
[RECUPERACION_DISENO_WEB.md](docs/RECUPERACION_DISENO_WEB.md).

Los apartados siguientes conservan la historia de la versión Spring Boot.
Sus cuentas, vínculos y preparación Supabase/Render **no describen el acceso actual**.

Origen del compañero: https://github.com/luisgustavosalcedo53-sys/dispensalud-proyect,
rama `main`, conservado como remoto `origin`. La copia personal añade el remoto
`personal` y preserva historial, autores y atribuciones. No se cambia el repositorio
del compañero. No se encontró licencia general del proyecto; esta copia privada
no añade una licencia ni amplía derechos sobre código, imágenes o marcas. Los
avisos existentes de Inter, Bootstrap y marcas se conservan; ver
[procedencia y licencias](docs/PUBLICACION_PRIVADA.md#procedencia-y-avisos).

## Historia de la versión Spring Boot (fuera del runtime actual)

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

## Pendientes actuales

Integración y pruebas del hardware real, IA/OCR, notificaciones persistentes y
publicación Android en Play Store con firma de distribución y revisión de
privacidad. El APK de la Release Android sigue siendo un prototipo debug de
pruebas. Los apartados Spring Boot anteriores se conservan como historia y no
deben usarse para configurar la web Firebase desplegada.

