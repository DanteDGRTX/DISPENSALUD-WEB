# Informe consolidado DispenSalud

Noviembre de 2026. Corte documental de la integración local de interfaz.

DISPENSALUD

Informe integral del proyecto

Software, arquitectura, interfaz, despliegue y próximos pasos

Noviembre de 2026 | Integración local del aporte visual del equipo

Nueva portada integrada. Evidencia local: no es una captura de la versión publicada en Render.

Resultado principal

Una plataforma web funcional de organización y acompañamiento, con cuentas separadas, API Java y base externa preparada. Se integra la presentación del compañero sin sustituir la lógica de cuidado existente.

Límite del informe: describe lo implementado y probado, lo reportado durante el despliegue anterior y lo que continúa pendiente. No es una certificación clínica ni una auditoría integral de seguridad.

01 / Resumen y recorrido

DispenSalud busca facilitar la organización de los horarios de medicación de personas mayores y el acompañamiento de cuidadores o familiares. La solución proyectada combina plataforma web, aplicación Android y un dispensador con control ESP32. Hoy el avance comprobable se concentra en la web y su infraestructura; el dispositivo todavía no está integrado a la API.

Etapa | Trabajo realizado | Evidencia y límite
Base del software | Django para el portal; Spring Boot para autenticación, permisos y datos del cuidado. | Código y pruebas locales.
Primeros flujos | Medicamentos, horarios, edición, pausa/reactivación, historial y ayuda. | Pruebas API y Django; persistencia local.
Infraestructura | Repositorio privado, Docker, despliegue en Render y PostgreSQL en Supabase. | En octubre se verificó salud HTTP y tablas; el usuario confirmó el flujo publicado.
Acceso a la base | SSL exigido y dos usuarios separados para negocio y sesiones. | El asistente local informó éxito y comprobó conexiones TLS/permisos.
Integración actual | Portada del equipo, Mi cuenta separada y registro de desarrollo. | 56 pruebas aprobadas, flujo HTTP local y revisión de escritorio/móvil. Sin nuevo despliegue.

Qué significa funcional

Los formularios de cuidado existentes guardan información y aplican permisos en el servidor. No son una maqueta de botones. Eso no implica que la web mueva el mecanismo, detecte una pastilla o confirme que la persona la tomó. El registro nuevo crea cuentas reales en el entorno local, sin vínculos automáticos ni envío de correo.

No se realizó en esta integración un nuevo diagnóstico de disponibilidad de Render/Supabase, una actualización del servicio público ni una comprobación de facturación. El despliegue previo y esta copia local deben distinguirse.

02 / Arquitectura y responsabilidades

Flujo principal: navegador -> portal Django -> API Spring Boot -> PostgreSQL. El código se mantiene en la carpeta local y se respalda mediante Git/GitHub; Render ejecuta una versión construida a partir del repositorio.

Componente | Responsabilidad | Ubicación
Interfaz | HTML, CSS y JavaScript. Portada, formularios y panel accesible. | web/portal/templates y static
Django 5.2.18 | Vistas, CSRF, sesiones de servidor y cliente HTTP de la API. | web; Gunicorn en Docker
Java 17 / Spring Boot 3.5.16 | Cuentas, autenticación, autorización por vínculo, validación y persistencia del negocio. | api; puerto interno 8080
PostgreSQL / Supabase | Datos de cuidado y almacenamiento de sesiones, en esquemas privados separados. | dispensalud_private y portal_private
Docker / Render | Construcción, arranque de Java y Gunicorn, salud y cierre coordinado. | Dockerfile y deploy/start.py
GitHub privado | Código versionado. No sustituye un respaldo de datos ni guarda los secretos. | luisgustavosalcedo53-sys/dispensalud-proyect

Desarrollo y nube

En la computadora, H2 conserva el negocio y SQLite las sesiones técnicas. En el perfil cloud se usa PostgreSQL: no existe respaldo automático a H2/SQLite si falla la conexión. El entorno local y el publicado no comparten registros de manera automática.

Dentro del contenedor de demo, Java escucha en loopback y Django es la entrada pública. Android necesitará una estrategia de exposición autenticada de la API; no basta asumir que el puerto interno ya es un endpoint móvil público.

03 / Datos y autorización

Tabla / grupo | Uso
accounts | Identidad, nombre de usuario, hash BCrypt y rol CAREGIVER u OLDER_ADULT.
care_links | Vínculo explícito cuidador-persona. No se concede por conocer un UUID.
auth_sessions / login_attempts | Tokens guardados como hash, vencimiento y contador de intentos por identidad.
medications / schedules | Indicaciones, hora local, fechas de validez y estado activo o pausado.
audit_events | Actor, acción, objeto, persona y momento del cambio.
help_requests | Solicitud abierta/resuelta y sus fechas; no es un servicio de emergencias.
flyway_schema_history | Historial de las tres migraciones de negocio existentes.
Sesiones Django | django_session, migraciones y content types en portal_private.

Reglas que conserva el sistema

- La persona usuaria consulta su propia información y puede solicitar ayuda; no modifica medicamentos ni horarios.
- El cuidador configura únicamente a personas vinculadas. Cambiar un identificador en la URL no concede acceso.
- La vista previa de persona mayor no transforma la identidad del cuidador ni habilita acciones del otro rol.
- Pausar/reactivar y resolver solicitudes respetan autorización e idempotencia en las operaciones comprobadas.

Las tablas se modifican por migraciones, no borrándolas para introducir un diseño nuevo. El registro de esta integración utiliza la estructura accounts existente y no requiere otra tabla de identidad.

04 / Funciones implementadas

Área | Disponible | Límite actual
Acceso | Ingreso, salida, roles y sesiones; registro local controlado. | Sin verificación de correo ni recuperación.
Medicamentos | Crear, consultar y editar indicaciones. | Sin validación clínica de dosis o interacciones.
Horarios | Programación diaria, intervalo de fechas y pausa/reactivación. | Sin editor completo de recurrencias o días de semana.
Persona mayor | Horario claro, próximo evento, indicaciones y ajuste A+. | Requiere evaluación de comprensión con usuarios reales.
Ayuda | Solicitar, consultar y marcar como atendida. | Actualización al consultar; no hay push ni atención garantizada.
Historial | Hasta 50 eventos de actividad y cambios. | No equivale a un historial clínico ni prueba de ingestión.
Interfaz del equipo | Portada, producto, selector de componentes, galería, FAQ y acceso a cuenta. | Sin pagos, pedidos comerciales ni formulario de contacto activo.

Información de demostración

Se redujeron las etiquetas repetidas de datos ficticios. La interfaz se presenta como una aplicación utilizable, con una indicación discreta de versión de evaluación. No se eliminan aclaraciones indispensables sobre funciones todavía no conectadas ni se simulan confirmaciones físicas.

Los registros de ejemplo se guardan de verdad en el entorno correspondiente. La identidad de las personas de evaluación y las indicaciones de ejemplo no constituyen datos clínicos validados.

05 / Integración visual del compañero

Fuente: APAG-DISPENSALUD-master.zip, entregado por Gustavo. Se examinó su estructura Django, modelos, vistas, formularios, plantillas, CSS, JavaScript e imágenes. El archivo original se mantuvo sin modificar en Descargas.

Mi cuenta: acceso independiente del inicio, con orientación para persona usuaria y cuidador.

- Se conservaron el lenguaje visual oscuro, los acentos azules, las imágenes y la identidad del aporte del equipo.
- Se adaptaron producto, beneficios, funcionamiento, galería y FAQ a las funciones y límites de nuestro sistema.
- La portada vive en /; el ingreso en /ingresar/; el alta en /cuenta/crear/ y el panel en /panel/.
- Se conserva compatibilidad con enlaces antiguos del panel, y los recursos se sirven localmente sin depender de Google Fonts.

No se importó el backend comercial ni su SQLite. El precio provisional, el carrito, los pedidos y el contacto requieren decisión del equipo y un flujo aprobado. Las imágenes de hardware se tratan como referencias del diseño, no como evidencia de fabricación o ensayos.

06 / Cuentas: alcance de la nueva opción

Sí es posible mantener la portada y entrar al sistema desde Mi cuenta. La selección visual de perfil orienta la entrada, pero el rol real procede siempre de la cuenta autenticada. No se envía un rol elegido en la portada para elevar permisos durante el ingreso.

Paso | Comportamiento comprobado
Crear cuenta | Nombre, usuario normalizado, perfil permitido, contraseña de al menos 12 caracteres y confirmación.
Guardar | La API guarda BCrypt y devuelve datos públicos de la cuenta, nunca su hash ni la contraseña.
Ingresar | Se utilizan las mismas sesiones y permisos de la API. El registro no inicia una sesión automática.
Persona usuaria nueva | Puede acceder a su propio espacio, inicialmente sin medicamentos ni horarios.
Cuidador nuevo | Panel vacío hasta que exista un vínculo autorizado. No ve cuentas ajenas ni a la persona demo.
Entorno alojado | Registro cerrado por defecto en web y API. La barrera adicional de demo no se retiró.

Habilitación controlada

DISPENSALUD_REGISTRATION_ENABLED regula el alta. Local permite evaluación por defecto; cloud deniega por defecto. No abrir el registro general sólo cambiando esa variable: faltan verificación de correo, recuperación, límites por origen y el flujo de invitación/aceptación/revocación.

La confirmación de uso de evaluación del formulario no sustituye una política de privacidad, consentimiento informado o base legal para procesar datos reales. No se implementó Google/GitHub como proveedor de identidad de las personas usuarias.

07 / Infraestructura y seguridad

- Contraseñas del producto con BCrypt; tokens aleatorios de API almacenados como hash, con revocación y vencimiento.
- Límite persistente por nombre de acceso: cinco intentos en quince minutos. Sesión inactiva tras treinta minutos y máximo absoluto de ocho horas.
- CSRF en Django; cookies seguras en producción, CSP, bloqueo de marcos y de permisos de cámara, micrófono y ubicación innecesarios.
- Conexiones PostgreSQL con verify-full y certificado; Supabase configurado para exigir SSL por el propietario.
- Esquemas privados sin acceso de anon/authenticated/PUBLIC y usuarios distintos para negocio y sesiones. El asistente no conserva la clave administradora.
- Secretos fuera de Git, imágenes Docker y archivos de respaldo. Variables de entorno y certificado de despliegue se gestionan por separado.

Riesgos pendientes que no deben ocultarse

Las claves que se compartieron anteriormente en el chat deben rotarse; no se copiaron a este informe ni al ZIP. Cambiar una variable de seed no cambia las contraseñas de cuentas ya creadas. Se necesita un procedimiento que actualice hashes, revoque sesiones y compruebe el acceso posterior.

Los usuarios de esta demo aún tienen permisos para migrar dentro de sus esquemas; para producción se deben separar migrador y ejecución. Falta revisar privilegios heredados, limitar conexiones de red con conocimiento de los orígenes de Render, añadir control por origen, monitoreo, privacidad y restauración probada de respaldos.

Ni el candado HTTPS, ni una consulta de salud correcta, ni un asesor automático sin alertas equivalen a seguridad absoluta o autorización para uso clínico.

08 / Pruebas y evidencia

Suite | Resultado | Cobertura principal
API Spring Boot | 16 aprobadas | Permisos, IDOR, datos, validaciones, sesiones, intentos, ayuda, registro sin vínculos y cierre de registro.
Django | 26 aprobadas | CSRF, paneles, preview, HTTPS, CSP, demo gate, salud, portada y formularios de registro.
Supervisor Docker | 6 aprobadas | Variables requeridas, TLS y URL sin secretos, cierre coordinado y fallo de procesos.
Asistente PostgreSQL | 8 aprobadas | TLS, permisos y archivos, rechazo de estados inseguros y diagnóstico sin revelar claves.
Total automatizado | 56 aprobadas | No sustituye pruebas de carga, pruebas con personas ni auditoría externa.

Prueba HTTP real adicional

Se ejecutó el portal local contra la API local: ingreso de cuidador existente, creación de una cuenta de cada rol, ingreso a ambos paneles y salida. El cuidador nuevo no recibió vínculos; la persona usuaria accedió a su propio espacio. Las cuentas de comprobación son locales y no se incluyen sus credenciales ni registros en el respaldo.

Revisión visual

Se revisó la portada a 1440 x 960 y 390 x 844, corrigiendo el ajuste de cabecera móvil. Se comprobó el menú móvil, el selector de componentes y las pantallas de ingreso/registro. Las capturas se conservan en previews. Los paneles mantienen tipografía y controles amplios; el cambio de paleta no elimina las restricciones de rol.

Límites: los tests API usan H2. La nueva integración no se ejecutó en PostgreSQL/Render durante este incremento. Tampoco se hicieron pruebas de correo, carga concurrente, entrega física, usabilidad con adultos mayores o Android.

09 / Lo que falta y orden de avance

Prioridad | Siguiente entrega | Criterio de cierre
1. Acceso seguro | Rotar secretos expuestos, correo, recuperación, invitaciones y revocación. | Cuentas independientes, pruebas de abuso y acceso cruzado denegado.
2. Interfaz | Validar con el equipo esta portada; probar navegación y lectura con personas mayores. | Observaciones incorporadas y evaluación de tareas básicas.
3. Publicación | Respaldar, revisar diff, autorizar push y desplegar una versión controlada. | Migraciones, salud, recursos y flujos verificados en nube; reversión posible.
4. Dispositivo | Identidad ESP32, ocurrencias de dosis, plan firmado/versionado, sensores y sincronización. | Sin doble entrega tras reinicio, control de vigencia y pruebas de energía/atascos.
5. Android | App Kotlin y avisos con credenciales propias y API autenticada. | Permisos solicitados cuando corresponden y pruebas reales de notificación.
6. Operación real | Privacidad, respaldo/restauración, monitoreo, disponibilidad y revisión profesional. | No basar tratamientos reales en una demo gratuita o mecanismo sin validar.

Diseño offline previsto, no implementado

El ESP32 debería ejecutar sólo un plan previamente sincronizado, vigente y con reloj confiable. Antes de accionar debe persistir el identificador de ocurrencia para no repetir una dosis tras reinicio; los eventos se subirán de forma idempotente. Si el plan vence, falla el reloj o el estado físico es incierto, se debe bloquear la entrega automática. Detectar salida o retiro no demuestra ingestión.

No se fijaron en este informe autonomía de batería, precisión mecánica, certificaciones, precio ni disponibilidad comercial: requieren evidencia y decisiones del equipo.

10 / Respaldo, continuidad y entrega

Carpeta de trabajo: C:/Users/Gustavo/Documents/Codex/2026-10-17/revisa-tod/outputs/dispensalud. El ZIP de entrega es un respaldo del código y recursos con la integración actual, incluidos los archivos locales todavía no subidos a GitHub.

Se incluye | Se excluye deliberadamente
api, web, Dockerfile, deploy y scripts | Contraseñas, archivos .env reales, tokens y certificados locales de data
Imágenes del equipo y estilos integrados | Bases H2/SQLite locales y registros de Supabase
Documentación e informe consolidado | Entornos virtuales, target, cachés, compilados y metadatos .git
Capturas de presentación y pruebas | Historial bruto del chat con claves o datos sensibles

Cómo retomar

- Extraer en una carpeta nueva. No sobrescribir sin comparar una copia de trabajo con cambios propios.
- Abrir DispenSalud.code-workspace en VS Code y leer CONTINUAR.md, INTEGRACION_INTERFAZ.md y DESPLEGAR_RENDER.md.
- Preparar Java/Maven y Python; crear el entorno virtual e instalar web/requirements.txt. Los scripts locales generan accesos nuevos en una copia nueva; no asumir que son los de la nube.
- Guardar secretos aparte, en un gestor seguro. El ZIP no restaura la base de datos, cuentas cloud, DNS ni configuración del proveedor.
- Una vez revisado: autorizar commit/push y despliegue. La versión nueva no está publicada por entregar este ZIP.

Fuentes: revisión del código local, pruebas ejecutadas, archivo APAG entregado por el usuario, documentación del proyecto y confirmaciones del despliegue anterior en esta conversación. No se exportaron las credenciales ni la conversación completa.

Conclusión: la presentación del equipo y el sistema de cuidado ya conviven en una sola base de código. Se conserva un inicio atractivo y el acceso privado queda separado, sin reemplazar permisos o prometer funciones físicas pendientes.
