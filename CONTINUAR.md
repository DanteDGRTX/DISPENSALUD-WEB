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

Web local funcional con cuentas separadas, medicamentos e indicaciones editables, horarios diarios con pausa/reactivación, historial, solicitudes de ayuda, buscador y vista previa de la persona mayor. Hay diez pruebas de API y ocho de Django aprobadas. Consulta `docs/ESTADO.md` para los detalles y límites actuales.

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

1. Incorporar las observaciones del usuario sobre el diseño y los flujos.
2. Completar edición de horarios, registro/recuperación de cuentas y vínculos cuidador-persona.
3. Conectar y comprobar Supabase; la conexión externa todavía no está realizada.
4. Implementar Android Kotlin y notificaciones usando la misma API.
5. Implementar estados de dosis e integración offline del ESP32 con pruebas del mecanismo.
6. Mantener sincronizado el repositorio privado https://github.com/luisgustavosalcedo53-sys/dispensalud-proyect, vinculado como `origin` a la rama `main`. La cuenta se autentica mediante Git Credential Manager de esta laptop.

No es necesario rehacer la estructura ni empezar desde cero. Retomar leyendo este archivo y `docs/ESTADO.md` antes de editar.
