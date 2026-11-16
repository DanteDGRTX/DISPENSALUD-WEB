# DispenSalud — paquete local de producción

Versión exacta: `@WEB_COMMIT@`, rama
`feature/firebase-web`. Frontend construido en Windows y comparado con Git.
No se realizó conexión, instalación ni cambio alguno en AWS.

- [Instalación y reversión](docs/INSTALACION_Y_REVERSIÓN.md): dos fases, app primero
  y www después; conserva los cuatro hosts y servicios AgroSmart.
- [Compatibilidad y límites](docs/COMPATIBILIDAD.md): metadatos Python 3.14,
  advertencia Gunicorn, recursos y comprobaciones locales frente a pendientes.
- `RELEASE.json`: procedencia, commit, hashes de fuentes y tamaños.
- `DEPENDENCY_AUDIT.json`: wheels fijados, metadatos y SHA-256.
- `SHA256SUMS`: integridad de todos los archivos, salvo el propio índice.
- `WINDOWS_VALIDATION.json`: resultados locales, no una ejecución Ubuntu.
- `ops/`: configuraciones nuevas y diagnósticos. No hay un instalador que active
  automáticamente servicios, cambie Nginx o solicite certificados.

Validación inicial: `https://app.dispensalud.site`. Dirección definitiva:
`https://www.dispensalud.site`; raíz redirige a www. Backend solo en
`127.0.0.1:8002`, un worker, unidad `dispensalud-web.service`.

La plantilla `.in` raíz/www no puede habilitarse tal cual: faltan las rutas TLS y
el bloque existente, que solo pueden inventariarse cuando se autorice acceso.
No modificar archivos compartidos ni certificados existentes por suposición.

## Reproducir en Windows

En un checkout limpio del commit exacto, con las dependencias frontend instaladas
según `web/package-lock.json` y el Python de build registrado en RELEASE.json:

```powershell
D:\dispensalud-web\web\.venv\Scripts\python.exe reproduce\prepare_release.py --repo D:\dispensalud-web --output-dir D:\otra-carpeta-nueva-de-paquetes --recipe-dir reproduce
```

Ejecutar desde la carpeta de este paquete. El destino debe estar FUERA de Git y
ser nuevo. La receta ejecuta el build Windows, exige que coincida con el commit,
extrae una lista permitida de fuentes, obtiene solo los wheels fijados por sus
URLs/hashes, recopila estáticos, comprueba producción localmente, audita exclusiones
y crea el tar dos veces para verificar que sus bytes sean idénticos.

Para conservar los mismos bytes también hay que conservar versiones del build y
las entradas de receta/metadatos; variar el Python de validación cambia su informe
y por tanto el hash. La instalación de producción, en cambio, usa exclusivamente
los wheels incluidos y hashes fijados, sin consultar índices ni construir código.

No se incluyen `.git`, venv, node_modules, frontend fuente, pruebas/fixtures del
proyecto, credenciales, bases ni logs. La configuración Firebase pública que ya
forma parte del bundle no es una cuenta administrativa ni una clave de servidor.
La clave Django se genera exclusivamente en el servidor mediante create_env.py.
