# Instalación y reversión — instrucciones, NO ejecutadas

Release de la web: `@WEB_COMMIT@`.
Python objetivo confirmado: **3.14.4**, Ubuntu **26.04 LTS**. RAM 908 MiB,
aproximadamente 340 MiB disponibles, 2.8 GB libres y sin swap. Volver a medir.
No instalar Node, Java, Spring Boot, emuladores ni dependencias de desarrollo.
No ejecutar apt upgrade, reinicio del host, Docker ni cambios en swap.

## Alcance y fases

1. Validación aislada: único archivo NUEVO Nginx `dispensalud-web`, único servicio
   NUEVO `dispensalud-web.service`, backend `127.0.0.1:8002`, host
   `app.dispensalud.site`, certificado NUEVO exclusivo de ese host.
2. Tras validar y autorizar la migración: web definitiva en
   `https://www.dispensalud.site`; raíz `dispensalud.site` redirige a www.
   Modificar únicamente los bloques raíz/www existentes, con respaldo y reversión.
   No habilitar un segundo vhost que duplique esos nombres.

Durante la fase 1 no modificar estos archivos:

- `/etc/nginx/sites-available/dispensalud-subdominios`
- `/etc/nginx/conf.d/dispensalud.conf`

Conservar los cuatro subdominios AgroSmart, Node-RED, Mosquitto, puertos, flujos,
credenciales, certificados y dominios ajenos. Si el bloque raíz/www reside dentro
de un archivo protegido, detener la fase 2 para resolver el alcance antes de editar:
no reemplazar el archivo compartido ni asumir una excepción de autorización.

## 0. Inventario de solo lectura y respaldo privado, tras autorización

Esta preparación no se conectó a AWS. Antes de instalar, identificar el host,
arquitectura, bloques raíz/www y los CUATRO nombres AgroSmart reales; no se han
inventado sus nombres. Registrar estado, HTTP/TLS y puertos de esos cuatro hosts
y de Node-RED/Mosquitto como línea base para comparar después de cada recarga.
No pegar flujos, claves, `nginx -T` ni variables privadas en el chat o repositorio.

```bash
sudo bash ops/preflight.sh
uname -m
free -m
df -h / /srv
sudo ss -ltnp
sudo systemctl is-active nginx nodered mosquitto  # adaptar nombre Node-RED al real
sudo nginx -t
command -v certbot  # si falta, detenerse; no instalar ni actualizar automáticamente
sudo certbot certificates  # solo inventario, no solicita ni modifica certificados
```

Guardar copia con permisos root-only en una carpeta NUEVA con fecha. Copiar
`/etc/nginx` preservando symlinks, unidad web anterior si existiera y los bloques
raíz/www exactos. Guardar `nginx -T` en ese respaldo privado, no en consola; anotar
cuáles archivos aportan los bloques y las rutas de certificados existentes.
Guardar SHA-256 de los dos archivos protegidos y repetirlo tras la fase 1: deben
coincidir. Conservar registro de los cuatro hosts, sus certificados y respuestas.
No copiar ni modificar llaves de certificados o credenciales AgroSmart.

**Detenerse** si 8002, el nombre del servicio/vhost/usuario o la ruta de certificado
nueva ya están ocupados, hay nombres Nginx duplicados, faltan permisos o recursos,
o no se puede identificar y respaldar el bloque que se propone tocar. No detener
el proceso que ocupe un puerto ni modificar servicios ajenos para hacer espacio.

## 1. Verificar e instalar una release nueva sin activarla

Transferir el `.tar.gz` y su `.sha256` por un canal autorizado. No usar git en AWS.
Primero ejecutar `sha256sum -c <archivo.tar.gz.sha256>` desde su directorio.
El `.sha256` debe obtenerse por un canal confiable; integridad no equivale a firma.

Comandos de ejemplo, ejecutar solo tras el inventario. No sobrescriben una release:

```bash
COMMIT=@WEB_COMMIT@
ARCHIVE=/ruta/subida/dispensalud-web-${COMMIT}.tar.gz
RELEASE=/srv/dispensalud-web/releases/${COMMIT}
# Confirmar que estos nombres no existen antes de crearlos.
sudo useradd --system --user-group --home-dir /nonexistent --shell /usr/sbin/nologin dispensalud-web
sudo install -d -m 0755 /srv/dispensalud-web /srv/dispensalud-web/releases
sudo install -d -o dispensalud-web -g dispensalud-web -m 0700 /srv/dispensalud-web/shared
sudo install -d -o root -g root -m 0700 /etc/dispensalud-web
sudo mkdir -m 0755 "$RELEASE"  # falla si existe; no borrar para repetir
sudo tar --extract --gzip --file "$ARCHIVE" --strip-components=1 --directory "$RELEASE" --no-same-owner
cd "$RELEASE"
sudo sha256sum -c SHA256SUMS
sudo python3.14 ops/create_env.py  # genera la clave EN EL SERVIDOR, sin mostrarla
sudo sh -c 'umask 022; python3.14 -m venv "$1/.venv"' sh "$RELEASE"
sudo "$RELEASE/.venv/bin/python" -m pip install --no-index --find-links "$RELEASE/wheelhouse" --only-binary=:all: --require-hashes --no-cache-dir --no-compile -r "$RELEASE/requirements-production.txt"
sudo "$RELEASE/.venv/bin/python" -m pip check
sudo bash "$RELEASE/ops/manage-production.sh" migrate --noinput
sudo bash "$RELEASE/ops/manage-production.sh" check --deploy --fail-level ERROR
sudo bash -c 'set -a; source /etc/dispensalud-web/web.env; set +a; export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1; cd "$1/web"; exec runuser -u dispensalud-web -- "$1/.venv/bin/gunicorn" --config "$1/ops/gunicorn.conf.py" --check-config config.wsgi:application' sh "$RELEASE"
```

No hace falta Node/npm ni `collectstatic` en AWS: recursos compilados y estáticos
recopilados/comprimidos están incluidos. Wheels universales y nativos Linux x86_64/aarch64 permiten instalación
sin compilador, sin índice PyPI y sin dependencia de x86/ARM. El Python del host
debe incluir venv, ensurepip, sqlite3 y ssl; preflight lo comprueba.

La carpeta de release debe ser root-owned y legible por el usuario del servicio
y por Nginx (directorios 0755, archivos públicos 0644); nunca escribir secretos
allí. Solo `/srv/dispensalud-web/shared` y el directorio runtime del servicio son
escribibles por la aplicación. SQLite guarda sesiones técnicas, no Firestore.
En actualizaciones, conservar `/etc/dispensalud-web/web.env` y shared; **no volver
a generar la clave**. No usar el archivo `web/requirements.txt` histórico.

## 2. Arrancar únicamente el servicio nuevo y verificar loopback

Guardar primero el destino previo de `current`, si existe. Para primera instalación
se exige que `current` y `current.next` no existan; en actualización comprobar que
`current` sea un symlink propio antes del cambio atómico. Respaldar la unidad
anterior si existe; no sobreescribir una unidad ajena con el mismo nombre.

```bash
sudo ln -s "$RELEASE" /srv/dispensalud-web/current.next
sudo mv -T /srv/dispensalud-web/current.next /srv/dispensalud-web/current
sudo install -m 0644 ops/dispensalud-web.service /etc/systemd/system/dispensalud-web.service
sudo systemd-analyze verify /etc/systemd/system/dispensalud-web.service
sudo systemctl daemon-reload
sudo systemctl start dispensalud-web.service
sudo systemctl status dispensalud-web.service --no-pager
curl --fail --silent --show-error -H 'Host: app.dispensalud.site' http://127.0.0.1:8002/salud/
curl --fail --silent --show-error -H 'Host: app.dispensalud.site' -H 'X-Forwarded-Proto: https' http://127.0.0.1:8002/ingresar/ -o /dev/null
sudo ss -ltnp 'sport = :8002'
sudo systemctl show dispensalud-web.service -p MemoryCurrent -p MemoryPeak -p TasksCurrent
free -m
```

No usar `systemctl enable --now` antes de revisar el arranque real de Gunicorn
con Python 3.14.4. Tras pasar todas las validaciones, habilitar únicamente esta
unidad. Tiene un worker sync, límite por grupo de 192 MiB y MemoryHigh 128 MiB;
son límites conservadores, no mediciones ni garantía de capacidad. Si falla/OOM,
detener solo este servicio, conservar logs privados y medir; no elevar límites,
crear swap ni detener otros servicios automáticamente. No usar recarga USR2 ni
dos releases simultáneas en esta RAM: parar/arrancar solo esta unidad al actualizar.

## 3. Host app y certificado independiente por webroot

Confirmar A/AAAA de `app.dispensalud.site` y que alcanzan esta instancia (IPv6
incorrecto debe corregirse o quitarse con autorización DNS; no inventar IPv6).
Los ejemplos no añaden listen IPv6 sin inventario. Verificar también que Nginx
carga sites-enabled y que nadie usa ya `app.dispensalud.site`.

Antes de solicitar el certificado, inspeccionar `cli.ini` y hooks Certbot de
directorio y configuración. No ejecutar si alguno puede modificar/reiniciar
servicios ajenos; resolver primero el aislamiento. `--no-directory-hooks` evita
los hooks compartidos de directorio, pero no sustituye esa revisión de configuración.
Confirmar que el Certbot ya instalado admite la opción; si no, detenerse sin actualizar.

```bash
sudo install -d -m 0755 /var/www/dispensalud-web-acme/.well-known/acme-challenge
sudo install -m 0644 ops/nginx/dispensalud-web.http-validation /etc/nginx/sites-available/dispensalud-web
sudo ln -s /etc/nginx/sites-available/dispensalud-web /etc/nginx/sites-enabled/dispensalud-web
sudo nginx -t
sudo systemctl reload nginx  # solo si nginx -t pasa sin conflictos
# Confirmar desde fuera que un token de prueba NUEVO en el webroot es accesible.
sudo certbot certonly --no-directory-hooks --webroot --webroot-path /var/www/dispensalud-web-acme --cert-name dispensalud-app-validation -d app.dispensalud.site
```

Si falta aceptación de términos/correo ACME, corresponde al propietario. No usar
`--nginx`, `--apache`, `--standalone`, `--expand`, certificados wildcard ni añadir
otros dominios a esta solicitud. No parar Nginx ni tocar los certificados existentes.
Comprobar SAN y rutas del certificado nuevo: solo `app.dispensalud.site`.

Respaldar el archivo nuevo HTTP antes de cambiarlo a HTTPS:

```bash
sudo install -m 0644 ops/nginx/dispensalud-web /etc/nginx/sites-available/dispensalud-web
sudo nginx -t
sudo systemctl reload nginx  # solo tras revisión correcta
curl --fail --silent --show-error https://app.dispensalud.site/salud/
curl --head https://app.dispensalud.site/ingresar/
```

Revisar CSS/bundle/imágenes HTTP 200, móvil, cabeceras, certificado y ausencia de
bucles. No abrir 8002 en firewall ni Security Groups: solo 80/443 en el perímetro
ya autorizado. Nginx sobrescribe Host y X-Forwarded-Proto; Gunicorn confía solo en
loopback. No añadir CORS global ni debilitar CSP. Repetir hashes protegidos y
sondeos de los cuatro hosts AgroSmart/Node-RED/Mosquitto y comparar con línea base.

El sitio nuevo no guarda access logs; su error log tiene configuración separada
`ops/dispensalud-web.logrotate`, que puede instalarse como archivo NUEVO en
`/etc/logrotate.d/dispensalud-web` si logrotate ya existe. No cambiar retención
global ni rotación de AgroSmart. No registrar tokens, cuerpos ni datos clínicos.

Renovación: inspeccionar hooks/globales existentes ANTES de probar renovación,
porque podrían reiniciar servicios. No instalar un hook global. Programar una
prueba ACME solo del certificado nuevo tras esa revisión:
`certbot renew --no-directory-hooks --cert-name dispensalud-app-validation --dry-run`.
Una renovación real deberá validar `nginx -t` y recargar Nginx para leer el nuevo
certificado, por un mecanismo exclusivo de este certificado revisado previamente.
No modificar temporizadores, hooks ni certificados ajenos en esta entrega.

## 4. Firebase y pruebas reales antes de migrar

Revisar en el proyecto Firebase existente los dominios autorizados y, si aplica,
restricciones HTTP referrer de la API key para los tres hosts HTTPS. No desplegar
reglas, índices ni configuraciones de emulador. Configuración pública actual y
contrato por UID se conservan sin Firebase Admin ni cuenta de servicio.
Probar con autorización una cuenta ficticia, verificación/recuperación, perfil,
paciente/tratamiento, móvil, aislamiento de UID y cruce Android; limpiar solo el
fixture propio de forma controlada. Esas pruebas reales siguen pendientes.
Cambiar de app a www cambia el origen: puede requerir iniciar sesión de nuevo.

## 5. Migración final exclusiva de raíz/www

`ops/nginx/root-www-migration.conf.in` es una plantilla de revisión, NO un archivo
listo para habilitar. Las rutas TLS reales y el webroot de renovación del bloque
existente no se conocen sin inventario. Sustituir los marcadores con las rutas
existentes verificadas y preservar literalmente sus ubicaciones ACME, listen,
certificados y demás directivas. El certificado de app NO cubre raíz/www.
Si el certificado existente no cubre ambos nombres, detenerse para preparar un
certificado independiente raíz/www con autorización; nunca ampliar uno AgroSmart.

Tras respaldo y autorización, cambiar exclusivamente esos bloques existentes:
HTTP raíz/www → https www; HTTPS raíz → https www; HTTPS www → 127.0.0.1:8002.
No crear nombres duplicados ni cargar el `.in` como vhost nuevo. Validar `nginx -t`
y revisar avisos de conflicto antes de `systemctl reload nginx` (no restart).
Comprobar redirecciones conservando path/query, TLS de ambos hosts, www completo,
sesión Firebase y los CUATRO subdominios AgroSmart con la línea base.

## Reversión

Ejemplo de retirada de la fase 1, únicamente si esta instalación creó el vhost y
la unidad y se confirmó que no existía una versión anterior:

```bash
sudo systemctl disable --now dispensalud-web.service
LINK=/etc/nginx/sites-enabled/dispensalud-web
test "$(readlink -f "$LINK")" = /etc/nginx/sites-available/dispensalud-web || exit 1
# Deshabilitar conservando el enlace como evidencia FUERA de sites-enabled.
# Verificar que el destino de respaldo no existe; usar ruta nueva root-only.
sudo test ! -e /etc/dispensalud-web/disabled-nginx-link || exit 1
sudo mv -- "$LINK" /etc/dispensalud-web/disabled-nginx-link
sudo nginx -t
sudo systemctl reload nginx  # solo si la validación anterior pasa
```

Antes de ejecutar estos pasos, anotar el estado previo y confirmar el alcance.
Si nginx -t falla, reponer ese mismo enlace y revisar; no recargar una configuración
inválida. Comprobar los cuatro hosts AgroSmart con la línea base.

- Fallo de fase 1: parar únicamente `dispensalud-web.service`. Si es la primera
  instalación, deshabilitar únicamente el symlink NUEVO
  `/etc/nginx/sites-enabled/dispensalud-web` (verificar antes su destino),
  `nginx -t` y reload. Dejar archivos, certificado nuevo y shared para diagnóstico;
  no borrar ni revocar certificados automáticamente. Raíz/www y AgroSmart no se
  tocaron. Si había versión anterior del vhost nuevo, restaurar solo esa copia.
- Actualización de código: `systemctl stop dispensalud-web.service`; verificar
  el destino anterior propio bajo `/srv/dispensalud-web/releases/`; apuntar
  `current.next` a ese destino y moverlo atómicamente a `current`; restaurar la
  unidad previa si cambió, daemon-reload, y `systemctl start dispensalud-web.service`.
  Evita solapar workers. Comprobar salud, estáticos, memoria y app/www.
- Reversión de fase 2: restaurar exclusivamente los bloques raíz/www desde el
  respaldo, preservando cualquier modificación concurrente ajena del archivo.
  No restaurar `/etc/nginx` completo. `nginx -t`, revisar conflictos, reload,
  comprobar raíz/www y los cuatro hosts. Si el archivo compartido cambió después
  del respaldo, hacer reversión manual del bloque con diff; no copiarlo entero.
- Preservar clave Django, shared y certificados existentes. Las migraciones
  incluidas son solo las sesiones técnicas de Django, sin migraciones propias;
  no se prevén downgrades de esquema. Nunca revertir/borrar Firestore como parte
  de volver el frontend ni modificar Android, Mosquitto o Node-RED.

La ejecución real Ubuntu/Python 3.14.4, sintaxis Nginx/systemd del host, TLS, DNS,
consumo real y pruebas Firebase remotas son compuertas pendientes. Este paquete
por sí solo no acredita que el despliegue haya pasado esas comprobaciones.
