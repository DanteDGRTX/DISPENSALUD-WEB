# Ajustes visuales finales · 16 noviembre 2026

Cambios locales sobre `02fac62`, en `feature/firebase-web`, conservando el diseño
web y los flujos Firebase. Sin push, merge ni despliegue. La carpeta
`D:\dispensalud-web-original` no se modifica ni se necesita para esta revisión.

## Presentación

- Acceso: leyenda decorativa y `figcaption` eliminados, sin espacio reservado.
  Dispensador centrado, de 360 px de ancho en escritorio y hasta 220 px en móvil,
  limitado al ancho disponible, con proporción automática y sin altura fija.
- El PNG original mide 629×397; la figura visible ocupa aproximadamente
  `(176,47)` a `(507,369)`. Un SVG en línea usa el encuadre `168 39 348 339` para
  quitar únicamente márgenes transparentes, con espacio alrededor del dispositivo
  completo. No se edita el recurso ni se cambia su presentación en el panel.
- El formulario se centra verticalmente junto a la columna izquierda. En móvil
  mantiene una separación de 35 px y el título queda debajo de la cabecera.
- Beneficios: únicamente «Para la persona usuaria» y «Para el cuidador», en dos
  columnas iguales en escritorio y una columna en móvil. Todas las demás
  secciones, navegación y pie permanecen.
- Las ilustraciones existentes Usuario/Cuidador se muestran a 72×57,6 px en
  tarjetas, con contenido visible de unos 65×50 px. Se usan en acceso,
  beneficios, registro y selección de perfil. El perfil de cuenta también conserva
  su ilustración ampliada; la insignia de contexto usa un tamaño menor.
- El acceso muestra la selección con borde azul y `aria-current`; registro y
  perfil conservan sus radios y estado marcado. Iconos de pacientes, tratamientos,
  agenda, historial, alertas, edición y confirmación mantienen sus etiquetas y
  `aria-hidden`. No se repiten las ilustraciones de perfil en las acciones.
- Las etiquetas históricas de acceso/registro también dicen Usuario/Cuidador.
  Sus valores técnicos y permisos no cambian; no se añaden perfiles.

Los cambios en `main.js` se limitan a etiquetas/iconos HTML y a comunicar el
perfil seleccionado a la presentación. Sin cambios en las operaciones Auth,
repositorio, datos, sincronización, reglas Firestore o Android. «Sin dispositivo
vinculado» y las aclaraciones reales del equipo permanecen dentro del panel.

## Validación

Desde `web`, con la web local ya servida en 8000:

```powershell
npm run build
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test portal
npm test
npm run test:browser
npm run test:emulator
npm run test:visual:final
```

- Build correcto; Django sin incidencias y 36 pruebas correctas.
- 10 pruebas del contrato, 13 de Auth/Firestore y 4 recorridos de navegador:
  63 pruebas automatizadas correctas. Solo emuladores y datos ficticios.
- Revisión visual completa de portada, acceso y registro en 1440×1000, 390×844,
  320×740 y 768×1024. Sin desbordamiento, imágenes rotas ni errores JavaScript.
- Dos tarjetas de beneficios y solo Usuario/Cuidador en los selectores; iconos
  legibles, selección funcional y formulario de acceso con validación activa.
- Verificación de alta, recuperación, verificación de correo, restauración,
  edición, conflictos, registro manual, alertas, perfil y aislamiento por UID
  mediante la suite de navegador existente. A+ y navegación móvil siguen operativos.
- Capturas inspeccionadas del acceso y beneficios en escritorio/móvil, y de la
  portada completa hasta el pie. Se conserva el orden de las ocho secciones.

Capturas reales e informe de dimensiones: `previews/visual-final/`. Son archivos
locales de revisión, excluidos del commit; logs y salidas temporales están en
carpetas ignoradas. `DISPENSALUD_BROWSER` permite elegir otro Chromium;
`DISPENSALUD_PREVIEW_URL` cambia el origen de la revisión visual.

Revisar en http://localhost:8000/ingresar/ y
http://localhost:8000/#beneficios. No se utilizan cuentas ni datos reales.
