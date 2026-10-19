# Estado real del primer incremento

## Implementado y comprobable localmente

- API Spring Boot con inicio de sesión, tokens aleatorios guardados como hash, vencimiento y revocación.
- Cuentas ficticias independientes de cuidador y adulto mayor, con contraseñas almacenadas como hash BCrypt.
- Autorización en el servidor por vínculo cuidador-persona. La persona mayor sólo consulta su información.
- Medicamentos y horarios diarios con validación, persistencia y auditoría de creación.
- Migración Flyway como base para H2 y PostgreSQL. El perfil local usa H2 en disco.
- Portal Django con formularios, sesiones de servidor, protección CSRF y Bootstrap local.
- Panel de configuración para el cuidador y vista diaria con letra y controles grandes para el adulto mayor.
- Diseño adaptable inspirado en la referencia Figma revisada: tarjetas, navegación inferior móvil y lateral en escritorio, reloj y cuenta regresiva.
- Edición de indicaciones, consulta de horarios y pausa/reactivación con autorización e historial.
- Solicitudes de ayuda persistentes: la persona mayor registra una solicitud y el cuidador puede marcarla como atendida. Se consultan al actualizar el panel; no hay avisos push todavía.
- Buscador, diálogos de creación, ajuste A+ y vista previa de la persona mayor sin cambio de identidad.
- Scripts PowerShell de inicio local y credenciales ficticias aleatorias fuera de Git.

## Pendiente

- Conectar y comprobar PostgreSQL externo en Supabase. Hay configuración, todavía no un proyecto cloud conectado.
- Alta y recuperación de cuentas, invitaciones cuidador-persona, cierre de todas las sesiones y límites de intentos de acceso.
- Eliminación con historial, edición de horarios existentes, días de la semana y horarios más complejos.
- Ocurrencias persistentes de dosis y estados de dispensación/retiro. Hoy se muestran horarios programados, no confirmaciones físicas.
- Aplicación Android Kotlin y notificaciones.
- Identidad ESP32, firma de programación, reloj confiable, límite de vigencia offline y sincronización idempotente.
- Integración con sensores y mecanismo, pruebas de energía/atascos y evaluación de comprensión con personas mayores.
- Despliegue público: TLS, secretos, almacenamiento de sesiones de producción, respaldos, monitoreo y revisión para datos reales.

## Verificación realizada

- Código respaldado en el repositorio privado https://github.com/luisgustavosalcedo53-sys/dispensalud-proyect, rama `main`. Los accesos ficticios, claves y bases locales siguen excluidos de Git.

- Compilación y empaquetado de Spring Boot completados.
- Diez pruebas de integración de la API aprobadas: acceso anónimo, permisos, vínculos, altas, consulta diaria, validación, revocación, edición, pausa/reactivación y solicitudes de ayuda.
- Ocho pruebas de Django aprobadas: CSRF, permisos, vista simplificada, selección autorizada, vista previa sin cambio de identidad, estado de horario y formato de fecha en el navegador.
- Flujo HTTP real aprobado con los servicios locales: ingreso del cuidador, alta ficticia de medicamento y horario, ingreso independiente del adulto mayor y lectura del horario guardado.
- Pantalla de ingreso revisada visualmente en el navegador; la comprensión y accesibilidad para usuarios mayores todavía requieren evaluación con personas reales.
- Segunda iteración comprobada mediante HTTP real: edición visible entre cuentas, pausa/reactivación y ayuda con resolución. También se agregó un medicamento y un horario ficticios usando los formularios del navegador.
- Revisión visual en 390 × 844 y 1280 × 900; capturas en `previews/` y guía en `PROBAR_DEMO.md`. Referencia de diseño y decisiones en `DISENO.md`.
- Se comprobó que credenciales, sesiones, claves y bases locales estén excluidas de Git. No se ha probado una conexión real a PostgreSQL/Supabase.

## Django y Spring Boot

Django es el portal web y cliente de servidor de la API. Controla vistas, formularios, CSRF y sesiones web. Spring Boot posee las cuentas del producto, los vínculos, los medicamentos y los horarios. Django no modifica esas tablas mediante otro ORM.

SQLite en Django guarda sólo sus sesiones técnicas en desarrollo. H2 guarda los datos ficticios de negocio de la API en desarrollo. PostgreSQL en Supabase será la base externa de negocio; no debe afirmarse que está conectada hasta comprobarla. `.env.example` es una plantilla y no se carga automáticamente: las variables se configuran en el entorno de cada proceso.

## Referencias de compatibilidad

- Spring Boot: https://docs.spring.io/spring-boot/3.5/system-requirements.html
- Django 5.2: https://docs.djangoproject.com/en/5.2/releases/5.2/
- Versiones de Django: https://www.djangoproject.com/download/
