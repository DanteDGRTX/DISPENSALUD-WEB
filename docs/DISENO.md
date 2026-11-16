# Iteración visual y funcional con referencia de Figma

**Estado vigente (16 noviembre 2026, `feature/firebase-web`):** se recuperó el
diseño web original oscuro/azul, con cabecera/pie compartidos, navegación lateral
en escritorio y menú de secciones desplegable en móvil. Firebase conserva cuentas
y datos. Ver [RECUPERACION_DISENO_WEB.md](RECUPERACION_DISENO_WEB.md).
El resto de este documento describe la iteración histórica clara/verde.

Referencia revisada: https://www.figma.com/design/jVpjNHzLSR7VczygZo8i4R/Sin-t%C3%ADtulo?node-id=0-1

El archivo visible contiene plantillas móviles generales: dashboard, actividad, entrada y otras pantallas. Se revisó visualmente mediante acceso de invitado; no se modificó el Figma. No es una plantilla específica de medicación. Se adoptaron su organización por tarjetas, jerarquía tipográfica y navegación inferior para móviles, adaptadas a DispenSalud.

## Diseño compartido

- Fondo claro, tarjetas blancas, verde petróleo como acción principal y acentos suaves para distinguir secciones.
- Navegación lateral en escritorio e inferior en móviles; enlaces con nombre e icono y sección actual identificable.
- Formularios de medicamento y horario en diálogos, con controles etiquetados y cierre por teclado.
- Buscador, reloj local, cuenta regresiva hasta el próximo horario y transiciones discretas; se respeta la preferencia de reducir movimiento.

## Persona adulta mayor

- Tres opciones: Mi día, Indicaciones y Pedir ayuda.
- Nombre sencillo, hora grande, indicación completa y botón A+ para aumentar el texto.
- Solicitud de ayuda registrada de verdad y consultable por el cuidador. No realiza una llamada ni envía todavía avisos push.
- No aparecen controles de edición ni pausas del tratamiento.

## Cuidador

- Resumen diario, administración de medicamentos y actividad.
- Alta, búsqueda y edición de indicaciones, creación de horarios y pausa/reactivación.
- Historial de cambios y solicitudes de ayuda con acción para marcarlas como atendidas.
- Vista previa del diseño de la persona mayor sin cambiar la identidad ni los permisos de la cuenta.

## Alcance de la vista previa

Se puede abrir en http://127.0.0.1:8000. La interfaz actual es web adaptable con Django y Bootstrap. Define la dirección visual para Android; no es todavía una aplicación Kotlin instalada. Los datos siguen siendo ficticios y se guardan en la base local.

La conexión a Supabase, la aplicación Android y el firmware offline del ESP32 siguen pendientes. El diseño de la pantalla no acredita que una dosis haya sido dispensada o ingerida.
