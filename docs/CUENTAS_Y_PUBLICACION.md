# Preparación de cuentas y publicación

Estado: 18 de octubre de 2026. El proyecto sigue siendo una demo local con datos ficticios. Se creó el proyecto externo `dispensalud-demo` en Supabase, pero la aplicación todavía NO usa esa base y NO está publicada. Las cuentas de proveedores NO son las cuentas de cuidador y persona mayor del producto.

## Qué debe hacer el propietario

1. Supabase: el propietario confirmó su organización personal. La consulta de costo devolvió $0 mensuales para crear el proyecto. Se creó `dispensalud-demo` (`cgpdfmubokvmgiqpzalc`) en `us-east-1`, con estado `ACTIVE_HEALTHY`. No hace falta abrir otra cuenta. Esa cotización no garantiza que todos los usos futuros sean gratuitos: revisar límites antes de ampliar recursos. No se contratarán recursos de pago sin aprobación expresa.
2. Hosting: crear o conectar una cuenta de Render cuando preparemos el despliegue. El propietario inicia sesión, acepta las condiciones y autoriza únicamente el repositorio privado de DispenSalud, no todos sus repositorios. Revisar el plan y sus límites antes de confirmar recursos. No hace falta comprar un dominio para preparar la demo; se puede comenzar con la dirección que asigne el hosting.
3. Activar verificación en dos pasos en GitHub y en las cuentas de infraestructura que la admitan. Guardar sus códigos de recuperación fuera del repositorio.
4. Cuando se incorpore verificación y recuperación de cuentas, elegir un servicio de correo transaccional y autorizarlo. El correo personal del propietario no debe convertirse en una contraseña compartida de la aplicación.

No enviar contraseñas, tokens ni cadenas de conexión por el chat. Configurarlos en un gestor de secretos del hosting o en archivos locales ignorados. El proyecto de Supabase y el hosting deben quedar a nombre del propietario. No se necesita instalar Visual Studio adicional: el código ya es una carpeta local que se abre con VS Code.

Panel del proyecto: https://supabase.com/dashboard/project/cgpdfmubokvmgiqpzalc

Para la siguiente conexión, abrir Connect en el panel y preparar host, puerto y usuario para la conexión seleccionada, junto con la contraseña de base y su certificado. Si hace falta generar o restablecer la contraseña, hacerlo en el panel y guardarla sólo en los secretos del entorno. No pegar la cadena con contraseña en el chat. El conector de administración no entrega por sí mismo las credenciales JDBC de ejecución al proceso local.

Se reservó el esquema `dispensalud_private`, sin acceso de los roles `anon`, `authenticated` o `PUBLIC`; su preparación está reproducida en `api/deploy/supabase_bootstrap.sql`. El perfil cloud usa ese esquema tanto para JDBC como para Flyway. Las tablas de negocio y el historial Flyway se crearán por las migraciones de la API cuando se configure y pruebe la conexión real. No copiar manualmente las migraciones V1–V3 al editor SQL, porque eso desincroniza el historial de Flyway. No añadir este esquema a los esquemas expuestos por la Data API.

## Qué puedo avanzar sin esos servicios

- Programación local, diseño y pruebas automatizadas.
- Separación cuidador/persona mayor y comprobación de vínculos en el servidor.
- Seguridad de sesiones, validaciones y preparación de migraciones.
- Registro, recuperación e invitaciones con un transporte de correo de prueba, sin afirmar que ya se envían correos reales.

## Refuerzo implementado en este incremento

- Máximo de cinco intentos por nombre de acceso en una ventana de quince minutos. El sexto se rechaza con HTTP 429. Los contadores persisten en la base, usan un hash del identificador y no guardan contraseñas. El mismo tratamiento se aplica a cuentas inexistentes. Un ingreso correcto reinicia el contador.
- Una sesión de la API vence tras treinta minutos sin actividad, además del máximo absoluto de ocho horas. Una sesión inactiva no se reactiva presentando el token otra vez.
- Política de contenido que limita scripts y estilos al propio sitio; bloqueo de cámara, micrófono y geolocalización, que este portal no necesita; respuestas del portal sin almacenamiento en caché.
- En configuración de producción: redirección HTTPS, cookies seguras y HSTS inicial de una hora. La configuración del proxy de confianza se debe definir y verificar al desplegar; no se confía automáticamente en cabeceras aportadas por el visitante.

El límite por cuenta no sustituye límites por origen en el perímetro: puede usarse para bloquear temporalmente a una víctima cuyo nombre se conozca. Falta protección por origen y monitoreo antes de abrir el servicio. No se presenta este incremento como una auditoría completa ni como autorización para datos clínicos reales.

## Bloqueantes antes de una demo pública

- Completar alta, verificación de correo y recuperación de cuentas con tokens de un solo uso y vencimiento. Hoy sólo existen cuentas de prueba previamente configuradas.
- Invitación y aceptación explícita del vínculo cuidador-persona; revocación de vínculos y cierre de todas las sesiones. Nunca conceder acceso sólo por conocer el UUID de alguien.
- Política clara de privacidad y aceptación del uso de datos ficticios. Los permisos del navegador se solicitan sólo cuando una función los necesita, no todos al entrar. No pedir contactos, ubicación, cámara ni micrófono sin necesidad.
- Configurar PostgreSQL en Supabase con TLS y certificado verificado, esquema privado no expuesto por la Data API y credenciales de mínimos privilegios. No publicar tablas del negocio con lectura anónima ni poner una clave privilegiada en JavaScript.
- Separar la cuenta que realiza migraciones de la cuenta de ejecución. No usar permanentemente un usuario administrador de PostgreSQL para atender peticiones.
- Probar migraciones y flujos contra PostgreSQL real. Las pruebas actuales usan H2 y no demuestran compatibilidad operativa en Supabase.
- Elegir almacenamiento persistente/compartido para sesiones Django. SQLite local y H2 de desarrollo no deben subirse como la base de producción.
- Preparar servidor de producción, archivos estáticos, proxy TLS, comprobaciones de salud, secretos, límites por origen, logs sin tokens ni información sensible, monitoreo y restauración comprobada de respaldos. No publicar `runserver` de Django ni exponer directamente el puerto local de la API.
- Probar ingreso, permisos e intentos de acceso cruzado desde la dirección pública. Mantener datos ficticios y acceso de demostración controlado; no publicar las contraseñas locales.

## Referencias verificadas

- Conexiones PostgreSQL y elección de conexión directa o pooler: https://supabase.com/docs/guides/database/connecting-to-postgres
- Despliegues y conexión de repositorios en Render: https://render.com/docs/deploys
- Protección de autenticación y limitación de intentos: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
