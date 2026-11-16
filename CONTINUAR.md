# Dispensalud proyect — punto para retomar

## Estado vigente · 16 de noviembre de 2026

Trabajar en `D:\dispensalud-web`, rama `feature/firebase-web`. La web activa usa
Django para páginas/estáticos y Firebase Authentication/Firestore para cuentas y
datos compatibles con Android. No requiere Spring Boot ni Supabase. Los perfiles
Usuario/Cuidador no dan acceso a otras cuentas.

Se recuperó la presentación web original: portada, logotipo, cabecera, pie,
tipografía, tarjetas y distribución. Se conservan los flujos Firebase; se añaden
el dispensador y los iconos de perfil/navegación. `landing.css` se elimina
intencionalmente porque sobrescribía el diseño global; no quedan enlaces a ella.

Leer [recuperación del diseño](docs/RECUPERACION_DISENO_WEB.md),
[web/README.md](web/README.md) y [contrato Firebase](docs/FIREBASE_WEB.md).
Iniciar con `.\scripts\Start-Web.ps1`; revisar http://localhost:8000/ y
http://localhost:8000/ingresar/. Validación actual y comandos en la guía de
recuperación. Las pruebas reales web↔Android y el hardware siguen pendientes.

Al retomar, conservar los archivos modificados/nuevos y consultar `git status`.
`D:\dispensalud-web-original` es una referencia de solo lectura. Esta entrega es
local: sin push, merge ni despliegue. Capturas e informes temporales se conservan
localmente, excluidos del commit; no guardar secretos ni datos de usuarios en Git.

## Historial anterior · arquitectura Spring Boot

Los apartados siguientes documentan etapas previas, no el acceso ni los pendientes
de la rama Firebase actual. Sus autorizaciones de publicación no se aplican a esta
entrega local.

Actualización de acceso del 3 de noviembre: se retiró la ventana del navegador `revision` por solicitud de Gustavo. La portada es pública y los paneles conservan el inicio de sesión personal y sus permisos. Se cambiaron las contraseñas de las dos cuentas demo alojadas; no escribirlas en Git ni suponer que coinciden con la variable de creación inicial de cuentas. El registro público permanece cerrado. Ver `docs/ACCESO_PERSONAL.md`.

## Último incremento: interfaz del equipo, noviembre de 2026

Actualizado el 3 de noviembre: paneles de cuidador y persona usuaria unificados con la portada azul oscuro; etiquetas de evaluación retiradas; limpieza selectiva del contenido inicial con V4. 58 pruebas aprobadas. Revisar `docs/INTEGRACION_INTERFAZ.md` y las capturas `previews/panel-*.png`. Aplicación local activa en http://127.0.0.1:8000/panel/ al terminar esta sesión. La nube conserva el despliegue anterior.

Leer primero `docs/INTEGRACION_INTERFAZ.md`. Portada del aporte APAG integrada, Mi cuenta separada y registro local controlado en la API. Panel trasladado a `/panel/`, manteniendo compatibilidad con marcadores anteriores. 56 pruebas aprobadas y prueba HTTP real local. Esta integración está en la carpeta local y el respaldo, NO publicada en Render ni enviada a GitHub. Rotación de las claves compartidas anteriormente sigue pendiente; no escribirlas en documentación ni en el chat. Los estados y pendientes de apartados antiguos deben leerse como historial, no como verificación actual de la nube.

El código está guardado en esta carpeta. Abre `DispenSalud.code-workspace` en Visual Studio Code.

## Acuerdos del proyecto

- Dos cuentas y permisos distintos: cuidador y persona adulta mayor.
- El cuidador configura medicamentos, indicaciones y horarios; la persona mayor recibe una experiencia sencilla, legible y con controles grandes.
- Por ahora se usan exclusivamente datos ficticios. El diseño toma como referencia el Figma documentado en `docs/DISENO.md`.
- Django sirve el portal Bootstrap; Spring Boot mantiene la API, autenticación, permisos y datos de negocio.
- Android se desarrollará en Kotlin. PostgreSQL externo en Supabase sigue siendo la base objetivo.
- El ESP32 deberá poder ejecutar una programación previamente sincronizada y vigente sin Internet; su implementación y validación siguen pendientes.

## Avance guardado

Web local funcional con cuentas separadas, medicamentos e indicaciones editables, horarios diarios con pausa/reactivación, historial, solicitudes de ayuda, buscador y vista previa de la persona mayor. Hay trece pruebas de API, diecinueve de Django y seis del supervisor aprobadas. Consulta `docs/ESTADO.md` para los detalles y límites actuales.

## Volver a ejecutar

Desde esta carpeta, en dos terminales PowerShell:

```powershell
.\scripts\Start-Api.ps1
```

```powershell
.\scripts\Start-Web.ps1
```

Abre http://127.0.0.1:8000. Si los servicios ya están ejecutándose, basta con abrir esa dirección. Los accesos ficticios de esta laptop están en `data/acceso-local.json`, excluido de Git y del ZIP. Al extraer el ZIP en una carpeta nueva, el script de la API genera nuevos accesos locales.

## Próximos pasos

Se preparó un asistente local adicional en `scripts/Prepare-Supabase.ps1` y `scripts/prepare_supabase.py` para crear y verificar dos usuarios limitados de la demo sin guardar ni compartir la contraseña administradora. Cinco pruebas unitarias aprobadas. Este asistente aún NO se ejecutó contra Supabase: requiere entrada oculta del propietario en una terminal local. No asumir que ya existen los usuarios ni que está conectado el portal. Archivos del asistente y esta documentación están pendientes de respaldo remoto; los secretos generados seguirán fuera de Git.

Preparación Render en `docs/DESPLEGAR_RENDER.md`: Docker de Django/Gunicorn + API Java interna, sesiones PostgreSQL separadas, control HTTP Basic adicional para una demo restringida, comprobación de salud y cierre coordinado. Se generó `data/render.env` local, ignorado por Git y Docker. Faltan credenciales JDBC/portal, certificado, build real Docker y prueba del despliegue. El propietario autorizó commit y push de este incremento, NO contratar recursos ni publicar automáticamente.

El refuerzo de acceso está en `docs/CUENTAS_Y_PUBLICACION.md`. Se creó `dispensalud-demo` en Supabase en la organización confirmada por el propietario, con cotización de creación de $0/mes. Falta configurar las credenciales JDBC y probar la aplicación contra esa base. Registro, recuperación e invitaciones todavía no están implementados. No afirmar que existe una demo pública ni que la aplicación ya usa PostgreSQL. Los cambios de código de este incremento son locales hasta realizar un respaldo remoto autorizado.

1. Incorporar las observaciones del usuario sobre el diseño y los flujos.
2. Completar edición de horarios, registro/recuperación de cuentas y vínculos cuidador-persona.
3. Conectar y comprobar Supabase; la conexión externa todavía no está realizada.
4. Implementar Android Kotlin y notificaciones usando la misma API.
5. Implementar estados de dosis e integración offline del ESP32 con pruebas del mecanismo.
6. Mantener sincronizado el repositorio privado https://github.com/luisgustavosalcedo53-sys/dispensalud-proyect, vinculado como `origin` a la rama `main`. La cuenta se autentica mediante Git Credential Manager de esta laptop.

No es necesario rehacer la estructura ni empezar desde cero. Retomar leyendo este archivo y `docs/ESTADO.md` antes de editar.
