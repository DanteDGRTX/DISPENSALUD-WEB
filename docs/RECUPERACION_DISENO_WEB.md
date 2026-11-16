# Recuperación del diseño web · 16 noviembre 2026

Entrega local en `D:\dispensalud-web`, rama `feature/firebase-web`. Se revisaron
los cambios pendientes sobre `bb4fd4a` (documentación/validación Firebase) y
`3edbad8` (integración Firebase), contrastando la presentación con `e5df25c` y
`443dab6` (diseño web anterior). Se conservaron los archivos modificados y nuevos.
No se hizo push, merge ni despliegue.

## Presentación recuperada

- Portada con las mismas secciones y orden, paleta, tipografía, logotipo,
  cabecera, pie, composición y adaptación a móvil de la web original.
- `site_header.html` y `site_footer.html` extraen los componentes compartidos de
  `product_base.html`; las páginas Firebase extienden esa misma base. Sus enlaces
  a las secciones de portada son absolutos (`/#producto`, etc.) para funcionar
  también desde `/ingresar/` y el panel. El menú móvil conserva `aria-expanded`.
- `frontend/presentation.js` adapta acceso, registro y panel a la presentación
  original. Se usan el dispensador transparente original, los iconos de perfil
  y SVG de navegación. No se importan diseños de pantallas Android.
- La portada conserva aclaraciones sobre Firebase, cuentas propias, registro
  manual e integración física pendiente; no anuncia permisos ni funciones de la
  antigua API que esta versión no implementa.
- A+ amplía también títulos y controles definidos en `rem`, conserva el ajuste
  al navegar dentro del panel y permite volver al tamaño inicial. En móvil, los
  filtros pasan a una columna con A+ para evitar desbordamiento de campos de fecha.

## Eliminación intencional de `landing.css`

La hoja eliminada imponía Inter global, otro fondo, logotipos y alturas de imagen
con `!important`. Esos cambios reemplazaban la presentación web original. Se
retira su enlace de `product_base.html` y se conservan `product/reference.css` e
`integration.css` como estilos de portada, cabecera, pie y acceso.

`npm run build` genera dos archivos versionados que deben actualizarse junto con
las fuentes: `portal/static/portal/firebase/app.js` y `panel-web.css`. El segundo
combina Bootstrap local, `portal/app.css` y `product/panel.css`, limitando sus
selectores a `.web-workspace` mediante PostCSS. Conserva las reglas de keyframes
y evita que las reglas globales del panel cambien el resto del sitio.
`firebase/app.css` adapta diálogos, estados, filtros y controles Firebase.

No quedan referencias activas a la hoja eliminada. Las menciones en documentación
y la aserción negativa de Django son deliberadas. Los estáticos se comprueban
desde las páginas servidas, sin depender de `landing.css`.

## Firebase conservado

Sin cambios en `frontend/repository.js`, `contract.js`, `firebase-config.js`,
reglas Firestore ni rutas activas. Django sirve las carcasas públicas; Auth y
Firestore autorizan por UID y correo verificado. Se conservan registro,
recuperación, verificación, restauración/cierre de sesión, pacientes,
tratamientos, planificación de siete días, conflictos, historial manual,
alertas y preferencias. Usuario/Cuidador no concede acceso entre cuentas.

El menú lateral original se usa en escritorio y un menú desplegable de secciones
en móvil; no se añade una barra inferior fija. El equipo indica que no hay
dispositivo vinculado. No se confirma dispensación ni ingestión.

## Comprobaciones y reproducción

Desde `D:\dispensalud-web\web`, con dependencias instaladas y `.venv` preparado:

```powershell
npm run build
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test portal
npm test
npm run test:emulator
npm run test:browser
```

| Comprobación | Resultado |
|---|---|
| Build esbuild + PostCSS | Correcto |
| Django: comprobación y pruebas | Sin incidencias; 36 pruebas correctas |
| Contrato JavaScript | 10 pruebas correctas |
| Auth/Firestore y reglas locales | 13 pruebas correctas |
| Navegador con Auth/Firestore emulados | 4 recorridos correctos |
| Total automatizado | 63 pruebas correctas |
| Comparación visual | 12 páginas completas; escritorio 1440×1000 y móvil 390×844 |
| Portada original frente a recuperada | Mismo orden de secciones, tipografía, fondo y altura de cabecera |
| Navegador: panel y secciones | Móvil 390×844 y tablet 768×1024, sin desbordamiento ni imágenes rotas; A+ comprobado en escritorio y móvil |
| `localhost:8000`: rutas y estáticos fuente | 13 rutas y 27 recursos HTTP 200, configuración Firebase normal |

La suite de navegador cubre registro con confirmación incorrecta, verificación,
restauración, alta de paciente/tratamiento, planificación, registro manual,
conflicto con borrador conservado, desactivación, alerta leída, perfil, filtros,
salida, recuperación y aislamiento de un segundo UID. Usa exclusivamente
`demo-dispensalud-web`, datos marcados FICTICIO y correos `example.test`.

Requiere Java 21+, Auth 9098 y Firestore 8089 libres. La suite inicia/cierra su
Django temporal en 8002; deja intacto el servidor de revisión en 8000. Para
Chromium diferente de Brave, definir `DISPENSALUD_BROWSER` con su ejecutable.

La comparación opcional `npm run test:visual` requiere la web actual en 8000 y
la referencia ya servida en 8001. Solo lee las plantillas de
`D:\dispensalud-web-original` (o `DISPENSALUD_ORIGINAL`); renderiza el panel de
referencia con valores ficticios, sin consultar su base de datos ni iniciar
sesión. No se modifican archivos ni servicios de esa carpeta.

Capturas e informe: `previews/design-correction/`; HTML de comparación y logs:
`web/build/`. Se conservan localmente, ignorados por Git. La captura pendiente
`previews/design-original-login-desktop.png` también se conserva local e ignorada,
sin incluir archivos temporales en el commit. Dependencias, bases, secretos y
registros de emulador quedan excluidos.

Revisar en http://localhost:8000/ y http://localhost:8000/ingresar/. El puerto
8000 conserva la configuración Firebase normal; no se usaron cuentas reales.
La prueba real web↔Android, correo real, reglas publicadas y hardware siguen
pendientes; estos resultados no acreditan esas integraciones.
