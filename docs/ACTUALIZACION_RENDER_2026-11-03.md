# Actualización de Render — 3 de noviembre de 2026

Gustavo autorizó actualizar el servicio existente con la portada del equipo, las cuentas y los paneles unificados. La revisión previa confirma 58 pruebas aprobadas y respaldo de código sin secretos. El despliegue debe mantenerse en el servicio y plan existentes.

El contenedor compila Java y recoge los estáticos Django. Al iniciar, Flyway aplica V4: limpia únicamente nombres e indicaciones identificados del contenido inicial; conserva medicamentos ajenos a esos ejemplos, horarios, cuentas y contraseñas. No se importan las bases locales. El registro de nuevas cuentas permanece deshabilitado por defecto en cloud, como se documentó al implementarlo; no se altera la barrera de acceso ni las credenciales existentes.

Comprobaciones posteriores requeridas: commit desplegado en Render, respuesta saludable de `/salud/`, portada y recursos nuevos, acceso a ambos paneles y ausencia de errores al consultar los datos persistentes. La subida del código por sí sola no acredita estas comprobaciones.

El estado final de publicación se comunicará después de verificarlo en el servicio. Este documento registra la preparación, no una confirmación anticipada de éxito.
