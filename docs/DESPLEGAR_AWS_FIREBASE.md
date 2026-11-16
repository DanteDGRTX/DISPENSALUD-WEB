# Preparación AWS — NO ejecutada

La receta vigente para fotos privadas está en `deploy/release/prepare_release.py`
y sus entradas `deploy/release/inputs`: unidad **dispensalud-web.service**, un
worker en **127.0.0.1:8002**, validación app y migración delimitada raíz/www.
Los ejemplos antiguos siguientes de puerto 8000/dos workers no se usan en el
paquete actual. Ver `FOTOS_PRIVADAS_CONTRATO.md`; shared conserva las imágenes.

Este documento prepara la versión Django + Firebase, no la antigua demo Java.
No se accedió ni cambió AWS, DreamHost, DNS, reglas Firebase o sitios del equipo.
La IP de la captura **3.139.210.116 no se ha verificado**. No se afirma que esté
vigente ni que el servidor esté vacío. No usar `runserver` públicamente.

## Antes del despliegue autorizado

Confirmar cuenta AWS, región, instancia, sistema operativo, IP elástica asociada,
capacidad y arquitectura. Inventariar procesos/puertos, `systemctl`, contenedores,
vhosts Nginx/Apache, volúmenes, certificados, tareas y sitios existentes. Guardar
copia de sus configuraciones y resolver colisiones; no detener servicios ajenos.
Comprobar A/AAAA de ambos dominios y titularidad DNS. El proxy de ejemplo supone
Linux Ubuntu/Debian con systemd y Nginx; adaptar tras conocer el servidor.

Primero completar la prueba cruzada con Android descrita en FIREBASE_WEB.md.
Conservar el commit y release anterior para reversión. No desplegar una copia con
`DISPENSALUD_FIREBASE_EMULATORS=1` ni archivos `data`, `.env`, logs o fixtures.

## Dependencias y release

Python 3.13 + venv, dependencias fijadas en `web/requirements.txt`, Nginx, Certbot
con renovación systemd, y Node 22+ para **construir** estáticos. Java y Firebase CLI
son solo para pruebas con emulador, no para el servicio de producción. Spring
Boot, H2 y PostgreSQL/Supabase no se necesitan para cuentas/datos de esta versión.
El Dockerfile raíz y supervisor anteriores pertenecen a la demo y no se usan aquí.

Preparar un usuario de servicio `dispensalud` sin privilegios, un directorio de
releases `/srv/dispensalud/releases/<commit>` y datos técnicos persistentes en
`/srv/dispensalud/shared`. Apuntar `/srv/dispensalud/current` al release verificado.
Instalar un venv dentro del release y ejecutar desde su carpeta `web`:

```sh
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
npm ci --no-audit --no-fund
npm run build
# Con las variables de producción exportadas en este proceso:
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py check --deploy
```

Construir en CI/otra máquina compatible permite omitir Node/npm en el servidor.
WhiteNoise sirve los estáticos recopilados y comprimidos. No
publicar `node_modules`, pruebas ni el puerto de desarrollo. Mantener directorios
de release solo lectura para el proceso; `/shared` debe permitir escribir sus
sesiones técnicas SQLite. No se guardan datos clínicos en SQLite Django.

## Variables y servicio

Guardar `/etc/dispensalud/web.env` con propietario root, permisos restrictivos y
lectura solo donde el servicio lo necesite; no incluirlo en Git. Plantilla:

```text
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=GENERAR_UN_SECRETO_ALEATORIO_DE_AL_MENOS_50_CARACTERES
DJANGO_ALLOWED_HOSTS=dispensalud.site,www.dispensalud.site
DJANGO_CSRF_TRUSTED_ORIGINS=https://dispensalud.site,https://www.dispensalud.site
DJANGO_BEHIND_PROXY=1
DJANGO_DATA_DIR=/srv/dispensalud/shared
DISPENSALUD_FIREBASE_EMULATORS=0
DISPENSALUD_HOSTED_DEMO=0
```

`DJANGO_BEHIND_PROXY` confía en X-Forwarded-Proto solo porque Gunicorn escucha en
loopback y Nginx sobrescribe la cabecera. No habilitarlo si clientes externos
pueden alcanzar directamente el backend. Cookies técnicas Secure/HttpOnly/SameSite
Lax, CSRF Secure y redirección HTTPS se activan con DEBUG=0. Auth Firebase reside
en el navegador; no depende de una sesión Django ni de aceptar un UID por POST.
El registro Firebase está disponible independientemente del flag de registro de
la demo histórica. No hay variables de cuenta de servicio ni Firebase Admin.

Revisar [dispensalud.service](../deploy/aws/dispensalud.service), instalarlo solo
cuando sus rutas existan y habilitarlo tras validar el build. Utiliza Gunicorn en
**127.0.0.1:8000**, dos workers iniciales ajustables a capacidad medida.
No arrancar Spring Boot. Si otro sitio ya usa 8000, escoger otro loopback y cambiar
ambas plantillas coordinadamente.

## Proxy, DNS y TLS

Revisar [vhost Nginx](../deploy/aws/dispensalud.nginx.conf). Primero crear únicamente
un bloque HTTP con `server_name` de ambos dominios, el directorio ACME y ubicación
`/.well-known/acme-challenge/`. Mantener los vhosts restantes y el servidor por
defecto existentes. Verificar `nginx -t` antes de cada recarga.

Solo después de confirmar que DNS apunta a la instancia correcta, obtener el
certificado, por ejemplo `certbot certonly --webroot -w /var/www/dispensalud-acme
-d dispensalud.site -d www.dispensalud.site`. No ejecutar hasta la autorización de
despliegue. Cargar entonces el vhost HTTPS de ejemplo con rutas reales del cert.
Habilitar y comprobar el temporizador de Certbot; probar `certbot renew --dry-run`
y un hook que valide y recargue Nginx al renovar. HSTS inicial es 3600 segundos,
sin includeSubDomains/preload; revisar su incremento después de validar todo TLS.

Puertos públicos: **80 y 443**. SSH solo desde orígenes autorizados del equipo.
No abrir 8000, 8080, 8089, 9098, 4400 o 9150 en Security Groups ni firewall. El
navegador conecta por HTTPS a identitytoolkit.googleapis.com,
securetoken.googleapis.com y firestore.googleapis.com. No habilitar CORS global
ni debilitar CSP. La configuración web pública no sustituye las reglas por UID.

## Verificación posterior, logs y reversión

- Comprobar `systemctl status dispensalud`, `journalctl -u dispensalud`, acceso/
  error Nginx, TLS, renovación y ausencia de redirect loops. Evitar registrar cuerpos,
  tokens o datos de salud. Aplicar rotación y retención a logs del proxy.
- `/salud/` debe responder `{"status":"ok"}`. Es liveness de Django, no prueba de
  acceso a Firestore. Verificar CSS, bundle, fuentes e imágenes con HTTP 200.
- Probar ambos dominios, móvil, correo existente, verificación, recuperación,
  cambio de cuenta y edición ficticia en ambos sentidos con Android. Verificar
  errores de permisos/red, dosis sin duplicados y sin hardware inventado.
- Confirmar Firebase proyecto `dispensalud-130f5`, base `(default)`, dominios
  autorizados y restricciones de API key para el nuevo origen. No publicar las
  reglas de pruebas ni sobrescribir índices desde una configuración vacía.
- Reinicio ordinario: `systemctl restart dispensalud`, luego health y lectura real.
  Recarga Nginx solo tras `nginx -t`. No reiniciar indiscriminadamente el host.
- Reversión: reapuntar `current` al release anterior conocido, reiniciar únicamente
  este servicio y comprobar estáticos/TLS/sesión. No revertir ni borrar Firestore:
  las escrituras confirmadas permanecen y los clientes deben respetar el contrato.
  Conservar el mismo secreto y `/shared`; respaldar datos técnicos y configuración
  aparte del código. Mantener una copia controlada de reglas vigentes para revisión,
  sin cambiarlas como parte de revertir el frontend.

Ninguno de estos pasos se ejecutó contra infraestructura externa en esta entrega.
