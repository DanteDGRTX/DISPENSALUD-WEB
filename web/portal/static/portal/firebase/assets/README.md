# Recursos de la web Firebase

Los tres WebP se copiaron **sin modificar** desde los recursos corregidos de
Android (`D:\dispensalud-codex\app\src\main\res\drawable-nodpi`). Android se
consultó en modo de solo lectura. Se conserva el canal alfa y la proporción.

| Archivo | Dimensiones | Bytes | Procedencia |
| --- | --- | --- | --- |
| `brand_dispensalud.webp` | 281 × 246 | 9208 | Marca Dispensalud, fondo exterior transparente |
| `brand_tecsup.webp` | 707 × 213 | 44342 | Marca TECSUP, variante para fondo oscuro |
| `pillbox_pro.webp` | 779 × 896 | 605202 | Producto recortado, transparencia y proporción originales |
| `profile_user.svg` | viewBox 320 × 256 | 4350 | `drawable/profile_user.xml` |
| `profile_caregiver.svg` | viewBox 320 × 256 | 6948 | `drawable/profile_caregiver.xml` |

Los SVG trasladan literalmente los tres trazados de cada vector Android, sus
colores, alfa, grosores y terminaciones. No contienen fondos, fuentes, scripts ni
enlaces externos. Las imágenes JPEG adjuntas con cuadros no se usan como interfaz.

Los derechos de las marcas y del producto corresponden a sus titulares. Esta copia
no cambia su atribución ni implica licencia abierta sobre ellas.

## Inter

`InterVariable.woff2`: tipografía variable Inter (normal, pesos 100–900), 352240
bytes. Descargada el 16 de noviembre de 2026 del repositorio oficial:

- https://github.com/rsms/inter/blob/master/docs/font-files/InterVariable.woff2
- https://github.com/rsms/inter/blob/master/LICENSE.txt

Licencia SIL Open Font License 1.1 conservada en `Inter-LICENSE.txt`.
El archivo se sirve localmente: no hay solicitud a Google Fonts en el navegador.

SHA-256 de la copia incluida:
`693b77d4f32ee9b8bfc995589b5fad5e99adf2832738661f5402f9978429a8e3`.

```css
@font-face {
  font-family: Inter;
  font-style: normal;
  font-weight: 100 900;
  font-display: swap;
  src: url("./assets/InterVariable.woff2") format("woff2");
}
```

## Verificación

- Copias WebP idénticas byte a byte a Android; cabecera lossless VP8L con alfa.
- Producto y ambas marcas inspeccionados visualmente con `view_image`.
- Los tres `pathData`, trazos y transparencias de cada SVG coinciden exactamente
  con el XML Android; sin deformación del viewBox.
- Fuente con firma WOFF2 válida y licencia original incluida.
