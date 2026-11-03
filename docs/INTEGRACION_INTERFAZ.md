# Integración de interfaz del equipo - noviembre de 2026

## Actualización del 3 de noviembre: paneles unificados

Los paneles de cuidador y persona usuaria comparten la identidad azul oscuro del inicio: marca del equipo, tarjetas con degradados azules, navegación móvil inferior, formularios oscuros y transiciones que respetan la preferencia de movimiento reducido. Se conserva A+ para ampliar la lectura y los permisos diferentes de cada cuenta.

Se retiraron las etiquetas visibles de evaluación y los calificativos ficticios de los registros iniciales. La migración V4 actualiza únicamente las combinaciones identificadas del contenido inicial; no inventa tratamientos ni modifica registros ajenos a esos ejemplos. Los estados de dispositivo y horarios siguen reflejando sus funciones actuales. La confirmación del registro ahora recuerda el carácter personal de la cuenta y la privacidad de la contraseña; no constituye consentimiento clínico.

Validación actual: 17 pruebas API, 27 Django, 6 del supervisor y 8 del asistente PostgreSQL, todas aprobadas (58). Verificadas ambas sesiones y sus paneles en escritorio y celular, la ampliación de texto y la apertura del formulario de medicamento sin guardar datos nuevos. Evidencia: `previews/panel-cuidador-unificado.png`, `previews/panel-cuidador-movil.png`, `previews/panel-usuario-unificado.png` y `previews/panel-usuario-movil.png`.

Este cambio es local; no se envió a GitHub ni se desplegó en Render. El PDF consolidado corresponde al incremento anterior y se conserva como documento histórico; este apartado registra la actualización posterior.

## Fuente y criterio de integración

Se revisó APAG-DISPENSALUD-master.zip, entregado por Gustavo. Contiene una aplicación Django comercial/académica con portada, diseño azul oscuro, imágenes, exploración de componentes, galería, FAQ, contacto, pedidos y precio provisional editable.

Se conservaron la hoja de estilos de referencia y las imágenes en `web/portal/static/portal/product/`. Se adaptó la presentación a plantillas propias, sin ejecutar ni importar automáticamente el backend recibido. El aporte visual corresponde al compañero/equipo; no se atribuye su autoría a esta integración.

No se trasplantaron su SQLite ni sus claves, autenticación administrativa, carrito, cobros, cotizaciones o formularios de contacto. No se trasladaron afirmaciones de hardware implementado sin evidencia de validación. La portada distingue el concepto visual de las funciones comprobadas. No hay precio de venta fijado ni pagos habilitados.

## Rutas y cuentas

- `/`: portada con producto, beneficios, funcionamiento, especificaciones, galería y FAQ.
- `/ingresar/`: Mi cuenta. Elegir persona o cuidador no cambia los permisos del servidor.
- `/cuenta/crear/`: registro controlado con nombre, usuario, rol y confirmación de contraseña.
- `/panel/`: panel autenticado de cuidado, conservando sus funciones anteriores.
- Los marcadores antiguos `/?person=...&vista=...` redirigen al panel si hay sesión, sin permitir destinos externos.

La API Spring Boot guarda las cuentas con BCrypt. Django no introduce otra identidad. Sólo se admiten CAREGIVER y OLDER_ADULT, nunca administrador. No se crean vínculos de cuidado automáticamente. La persona usuaria accede a sí misma y un cuidador nuevo ve un panel sin personas vinculadas.

`DISPENSALUD_REGISTRATION_ENABLED` controla el registro. En desarrollo local se habilita por defecto; en cloud queda cerrado tanto en web como en API. Antes de habilitarlo públicamente faltan protección por origen, verificación, recuperación y consentimiento e invitaciones. La confirmación del formulario recuerda la privacidad de las credenciales, no es un consentimiento legal para datos reales.

La barrera HTTP Basic de la demo alojada permanece intacta. Este incremento no se publicó en Render ni se subió a GitHub. La versión anterior en Internet no cambia al editar la carpeta local.

## Verificación

- 16 pruebas API, 26 Django, 6 del supervisor y 8 del asistente PostgreSQL aprobadas: total 56.
- JavaScript comprobado sintácticamente y diff revisado.
- HTTP real local: cuidador existente; registro de ambos roles; ingreso a cada panel; cuidador nuevo sin vínculos y cierre de sesión.
- Revisión visual en 1440 x 960 y 390 x 844, menú móvil, selector del producto, ingreso y registro. Evidencia en `previews/integracion-*.png`.
- No equivale a auditoría de seguridad, evaluación con adultos mayores ni validación física.

## Respaldo

El ZIP conserva código, imágenes y documentación; excluye secretos, carpetas data, entornos virtuales, compilados y metadatos Git. No contiene un volcado ni registros de Supabase. Guardar las claves en un gestor seguro y respaldar/restaurar PostgreSQL por separado. El ZIP por sí solo no recupera los datos de la nube.
