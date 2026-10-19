# Dispensalud proyect — punto para retomar

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

Preparación Render en `docs/DESPLEGAR_RENDER.md`: Docker de Django/Gunicorn + API Java interna, sesiones PostgreSQL separadas, control HTTP Basic adicional para una demo restringida, comprobación de salud y cierre coordinado. Se generó `data/render.env` local, ignorado por Git y Docker. Faltan credenciales JDBC/portal, certificado, build real Docker y prueba del despliegue. El propietario autorizó commit y push de este incremento, NO contratar recursos ni publicar automáticamente.

El refuerzo de acceso está en `docs/CUENTAS_Y_PUBLICACION.md`. Se creó `dispensalud-demo` en Supabase en la organización confirmada por el propietario, con cotización de creación de $0/mes. Falta configurar las credenciales JDBC y probar la aplicación contra esa base. Registro, recuperación e invitaciones todavía no están implementados. No afirmar que existe una demo pública ni que la aplicación ya usa PostgreSQL. Los cambios de código de este incremento son locales hasta realizar un respaldo remoto autorizado.

1. Incorporar las observaciones del usuario sobre el diseño y los flujos.
2. Completar edición de horarios, registro/recuperación de cuentas y vínculos cuidador-persona.
3. Conectar y comprobar Supabase; la conexión externa todavía no está realizada.
4. Implementar Android Kotlin y notificaciones usando la misma API.
5. Implementar estados de dosis e integración offline del ESP32 con pruebas del mecanismo.
6. Mantener sincronizado el repositorio privado https://github.com/luisgustavosalcedo53-sys/dispensalud-proyect, vinculado como `origin` a la rama `main`. La cuenta se autentica mediante Git Credential Manager de esta laptop.

No es necesario rehacer la estructura ni empezar desde cero. Retomar leyendo este archivo y `docs/ESTADO.md` antes de editar.
