# Estado real del primer incremento

## Estado vigente de `feature/firebase-web` · 16 noviembre 2026

La rama local usa Django + Firebase Authentication/Firestore y recupera el diseño
web original. Se conservan las cuentas y el contrato Android, el aislamiento por
UID/correo verificado, pacientes, tratamientos, planificación, historial manual,
alertas y perfil. Spring Boot/Supabase pertenecen a la implementación histórica.
Usuario y Cuidador son preferencias de presentación, sin colaboración entre UIDs.

Cabecera/pie compartidos, estilos del panel limitados a `.web-workspace` y
eliminación intencional de `landing.css`, sin referencias activas. Se conserva el
dispensador original y los iconos necesarios. Guía y validación actual en
[RECUPERACION_DISENO_WEB.md](RECUPERACION_DISENO_WEB.md).

Revisión local en http://localhost:8000/. No se hizo push, merge ni despliegue.
Pendientes: prueba real de cuenta Android e intercambio web↔Android, revisión de
reglas/dominios Firebase publicados, colaboración entre cuentas e integración
ESP32. Las pruebas usan emuladores y datos ficticios, sin acreditar ingestión.

## Historial del primer incremento

Las cifras, servicios y pendientes siguientes son históricos; no reemplazan el
estado ni la validación actual de la rama Firebase.

## Actualización de noviembre de 2026

El despliegue anterior se verificó en octubre y el usuario confirmó su funcionamiento. Los apuntes que indican nube sin conectar corresponden a etapas anteriores. La nueva portada, Mi cuenta y registro de desarrollo se describen en `INTEGRACION_INTERFAZ.md`: implementados y probados localmente, todavía sin nuevo despliegue. Total actual: 56 pruebas automatizadas aprobadas. Registro público completo, correo, recuperación, vínculos por invitación y hardware siguen pendientes. Ver el informe PDF del respaldo para el estado consolidado.

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
- Límite persistente de intentos de ingreso por cuenta, vencimiento por inactividad y cabeceras de seguridad del portal. Detalles y límites en `CUENTAS_Y_PUBLICACION.md`.
- Preparación de despliegue restringido Docker para Render, con Java interno, Gunicorn, WhiteNoise, sesiones PostgreSQL y supervisor de procesos. Guía en `DESPLEGAR_RENDER.md`. Imagen y despliegue real todavía pendientes de comprobación.

## Pendiente

- Conectar y comprobar PostgreSQL externo en Supabase. Se creó el proyecto `dispensalud-demo` y se reservó el esquema privado, pero la aplicación todavía usa las bases locales; faltan credenciales JDBC y pruebas reales.
- Alta y recuperación de cuentas, invitaciones cuidador-persona, cierre de todas las sesiones y límites de acceso por origen en el perímetro.
- Eliminación con historial, edición de horarios existentes, días de la semana y horarios más complejos.
- Ocurrencias persistentes de dosis y estados de dispensación/retiro. Hoy se muestran horarios programados, no confirmaciones físicas.
- Aplicación Android Kotlin y notificaciones.
- Identidad ESP32, firma de programación, reloj confiable, límite de vigencia offline y sincronización idempotente.
- Integración con sensores y mecanismo, pruebas de energía/atascos y evaluación de comprensión con personas mayores.
- Despliegue público: TLS, secretos, almacenamiento de sesiones de producción, respaldos, monitoreo y revisión para datos reales.

## Verificación realizada

- Código respaldado en el repositorio privado https://github.com/luisgustavosalcedo53-sys/dispensalud-proyect, rama `main`. Los accesos ficticios, claves y bases locales siguen excluidos de Git.

- Compilación y empaquetado de Spring Boot completados.
- Trece pruebas de integración de la API aprobadas: incluye límites de intentos, reinicio de contadores, vencimiento por inactividad y los flujos anteriores.
- Diecinueve pruebas de Django aprobadas: incluye políticas del navegador, redirección HTTPS/HSTS, configuración PostgreSQL, filtro de demo y comprobación de salud, además de los flujos anteriores.
- Seis pruebas del supervisor: configuración requerida, TLS sin opciones contradictorias, credenciales fuera de URL, cierre, timeout y terminación de un componente.
- Flujo HTTP real aprobado con los servicios locales: ingreso del cuidador, alta ficticia de medicamento y horario, ingreso independiente del adulto mayor y lectura del horario guardado.
- Pantalla de ingreso revisada visualmente en el navegador; la comprensión y accesibilidad para usuarios mayores todavía requieren evaluación con personas reales.
- Segunda iteración comprobada mediante HTTP real: edición visible entre cuentas, pausa/reactivación y ayuda con resolución. También se agregó un medicamento y un horario ficticios usando los formularios del navegador.
- Revisión visual en 390 × 844 y 1280 × 900; capturas en `previews/` y guía en `PROBAR_DEMO.md`. Referencia de diseño y decisiones en `DISENO.md`.
- Se comprobó que credenciales, sesiones, claves y bases locales estén excluidas de Git. Se pudo administrar el proyecto nuevo de Supabase y verificar que su esquema privado no permite acceso a los roles de la Data API. La conexión JDBC de la aplicación a PostgreSQL todavía no se ha probado.

## Django y Spring Boot

Django es el portal web y cliente de servidor de la API. Controla vistas, formularios, CSRF y sesiones web. Spring Boot posee las cuentas del producto, los vínculos, los medicamentos y los horarios. Django no modifica esas tablas mediante otro ORM.

SQLite en Django guarda sólo sus sesiones técnicas en desarrollo. H2 guarda los datos ficticios de negocio de la API en desarrollo. PostgreSQL en Supabase será la base externa de negocio; no debe afirmarse que está conectada hasta comprobarla. `.env.example` es una plantilla y no se carga automáticamente: las variables se configuran en el entorno de cada proceso.

## Referencias de compatibilidad

- Spring Boot: https://docs.spring.io/spring-boot/3.5/system-requirements.html
- Django 5.2: https://docs.djangoproject.com/en/5.2/releases/5.2/
- Versiones de Django: https://www.djangoproject.com/download/
