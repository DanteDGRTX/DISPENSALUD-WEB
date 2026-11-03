# Acceso personal — 3 de noviembre de 2026

Gustavo solicitó eliminar la ventana de autenticación del navegador. Se retiró DemoAccessMiddleware y la exigencia de sus dos variables, tanto de Django como del supervisor y del generador de configuración nueva. El despliegue conserva HTTPS, CSRF, CSP, cookies de sesión seguras, protección contra intentos repetidos y permisos verificados en la API.

La portada, el ingreso y los archivos estáticos son públicos. `/panel/` redirige al inicio de sesión si no hay una cuenta autenticada. Enviar una cabecera Basic no da permisos de usuario. Crear cuentas desde Internet permanece deshabilitado por defecto.

Las contraseñas de `usuario.demo` y `cuidador.demo` se actualizaron en la base alojada con BCrypt y se revocaron sus sesiones previas. No se cambiaron las credenciales de PostgreSQL ni se pusieron contraseñas en el código o en una migración. La variable DISPENSALUD_DEMO_PASSWORD sólo se usa al crear la primera población en una base vacía; no restablece cuentas existentes ni es la referencia del cambio manual posterior.

Verificación de este incremento: 29 pruebas Django y 6 del supervisor aprobadas. Comprueban portada e ingreso sin desafío WWW-Authenticate, panel protegido, rechazo del registro público y conservación de cabeceras de seguridad. Las pruebas anteriores de API no requieren cambios porque su autenticación sigue igual. La confirmación de publicación se realiza después del despliegue en Render.

Los documentos PDF y registros de publicaciones anteriores se conservan como historial; sus referencias al filtro `revision` ya no describen el acceso actual.
