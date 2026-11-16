# Entrega privada — 16 de noviembre de 2026

Sitio público: **https://www.dispensalud.site**.
Fuentes personales privadas:

- Web: https://github.com/DanteDGRTX/DISPENSALUD-WEB, rama `feature/firebase-web`.
- Android: https://github.com/DanteDGRTX/DISPENSALUD-ANDROID, rama `master`.

## Versión y validación

El runtime web de fotos se cerró en
`3239f500b19ab39a94d037fab4b85729ae04886a`; Android en
`0689ec0bfe254b2159994a5d6f617f1fa5e959b2`. Los commits posteriores de publicación
documentan el estado y refuerzan exclusiones, conservando el código probado.

Se implementaron Authentication y Firestore compartidos, aislamiento por UID,
pacientes/tratamientos/horarios, registro manual/historial, alertas, perfiles de
presentación Usuario/Cuidador y recuperación del diseño web original. Las fotos
de cuenta y paciente ahora usan un índice privado Django, autorización por token
Firebase y propiedad del paciente, selección/previsualización/subida/reintento,
lectura autenticada, sustitución, borrado e iniciales como alternativa.

Pruebas locales completadas: 44 Django, 10 de contrato JS, cuatro recorridos de
regresión en navegador y el recorrido de fotos; Android 150 correctas/una omitida
y dos pruebas instrumentadas coordinadas con navegador real, Django Windows y
Auth/Firestore Emulator. Perfil y paciente se intercambiaron en ambos sentidos.
Se probaron otra cuenta, sustitución/borrado, archivos inválidos/grandes/cuota,
fallos de conexión/reintento, reinicio Django y persistencia Android tras detener
e instalar de nuevo con `install -r`. Se usaron imágenes y cuentas ficticias.

El usuario confirmó el 16/11/2026 que instaló la última versión en AWS y realizó
una prueba manual correcta de fotos Android ↔ web. Esta es una confirmación del
usuario, no una nueva ejecución/auditoría remota del agente. No se atribuyen a
esta publicación mediciones reales de memoria, compatibilidad de todos los
paquetes Linux, ni pruebas remotas adicionales.

## Configurar y ejecutar

[web/README.md](../web/README.md) describe el entorno Windows: Python 3.13, Node
22+, dependencias fijadas, `scripts/Start-Web.ps1`, build frontend y pruebas.
Dirección local `http://localhost:8000`. El servidor de producción no necesita
Node, Java, Spring Boot ni emuladores: recibe frontend y estáticos compilados.

Firebase mantiene el proyecto existente `dispensalud-130f5`, Authentication con
correo verificado y Firestore por UID. La configuración del SDK web es pública;
no es una cuenta de servicio ni autoriza por sí sola el acceso. Las restricciones
de API key/dominios deben corresponder al entorno. No desplegar reglas ni cambiar
Firebase como parte de publicar GitHub. En desarrollo aislado, las suites usan
únicamente `demo-dispensalud-web` y puertos 8089/9098.

`.env.example` contiene placeholders y no se carga automáticamente. Producción
requiere clave Django generada/mantenida en el servidor, `DEBUG=False`, los hosts
app/www/raíz, HTTPS/proxy/cookies/CSRF y `DJANGO_DATA_DIR` persistente. No versionar
web.env, claves, sesiones, datos clínicos ni respaldos. Los archivos operativos
de ejemplo están en [deploy/release/inputs/ops](../deploy/release/inputs/ops).

## Contrato de fotos y sincronización

[FOTOS_PRIVADAS_CONTRATO.md](FOTOS_PRIVADAS_CONTRATO.md) es el contrato v1. Perfil
`profile` y paciente `patient:<id>` son sujetos distintos. La referencia opaca
`private-photo:v1:<id-servidor>` se consulta en el índice común; no es una URI local,
una URL con token o base64. Firestore conserva `patients.body.foto:null`, sin
necesidad de nuevas reglas para fotos. El servidor no descarga URLs arbitrarias.

GET del índice/sujeto y GET de bytes requieren Bearer; PUT binario usa If-Match e
Idempotency-Key; DELETE usa If-Match. Se verifican identidad y autorización, tipo
real JPEG/PNG/WebP, <=2 MiB y dimensiones; se normaliza a JPEG <=512/128 KiB sin
EXIF. Cuotas 8 MiB/UID, 64 fotos/UID y 128 MiB total. La versión sustituida se
elimina tras confirmar. Los archivos viven en `shared/private-photos`, fuera de
releases y estáticos, sin alias público Nginx. Las URI locales Android antiguas
se conservan y solo se suben por petición explícita.

## Instalación, actualización y reversión

Receta reproducible Windows: [prepare_release.py](../deploy/release/prepare_release.py).
Se ejecuta desde un checkout limpio y genera fuera del repositorio un paquete del
commit exacto, con manifiesto y SHA-256. No requiere compilar frontend en AWS.
Guías operativas completas:

- [Instalación y reversión](../deploy/release/inputs/docs/INSTALACION_Y_REVERSIÓN.md).
- [Fotos persistentes y recursos](../deploy/release/inputs/docs/FOTOS_EN_DESPLIEGUE.md).
- [Compatibilidad declarada y sus límites](../deploy/release/inputs/docs/COMPATIBILIDAD.md).

Para una instalación nueva, seguir inventario y primera instalación de la guía.
Para el servicio ya instalado, **no repetir useradd ni create_env.py**: conservar
el usuario, `/etc/dispensalud-web/web.env`, clave Django y todo
`/srv/dispensalud-web/shared`. Verificar el archivo recibido y sus hashes, extraer
en una release NUEVA, instalar wheels offline en su venv y ejecutar las
comprobaciones de esa release sin activarla. Respaldar de forma privada la unidad
y el destino `current` antes de cualquier cambio autorizado.

Actualizar deteniendo solo `dispensalud-web.service`, cambiar `current` de forma
atómica a la release verificada y arrancar la misma unidad. Se mantiene un worker
y loopback `127.0.0.1:8002`; no solapar workers con esta RAM. Comprobar salud,
estáticos, fotos, memoria y aislamiento. Ante fallo, parar solo esa unidad y
restaurar el enlace/unidad previos; nunca borrar shared ni regenerar la clave.
Una release antigua sin API no verá fotos, pero debe conservar sus archivos.

No modificar Nginx al actualizar solo código. Para una futura migración de hosts,
app es validación con certificado exclusivo; www es canónico y la raíz redirige.
Cambiar exclusivamente sus bloques autorizados, respaldados, con `nginx -t` y
recarga revisada. Preservar los cuatro subdominios AgroSmart, Node-RED, Mosquitto,
certificados y archivos compartidos protegidos. Estas son instrucciones, no
acciones ejecutadas durante esta publicación.

## Release y revisión privada

Etiqueta nueva `web-fotos-privadas-20261116`. La Release adjunta el paquete original
del runtime `3239f50`, no una exportación de AWS, con SHA-256:

```text
b7c72d21099973bea98b89547139960c24db4968c55afabdd9ae60c524a48aa7
```

El manifiesto identifica el commit exacto del paquete. Sus instrucciones originales
reflejan la preparación previa al despliegue; la confirmación manual posterior
queda registrada aquí. No se afirma haber comprobado el hash instalado en AWS.

Antes de publicar se revisaron archivos actuales, historial alcanzable y los
entregables: sin llaves privadas, tokens, cuentas de servicio, `.env` con secretos,
google-services.json, local.properties, bases, fotos de usuarios, logs, respaldos,
venv, node_modules o builds versionados. Las capturas existentes muestran demos
ficticias y recursos del producto. La revisión estática no es una garantía absoluta
de ausencia de todos los posibles secretos; no se reescribe historia ni se fuerza
push. El tar lleva solo runtime/estáticos/wheels/operación, sin datos privados.

## Procedencia y avisos

Origen del compañero:
https://github.com/luisgustavosalcedo53-sys/dispensalud-proyect. Se conserva como
remoto `origin`; `personal` apunta únicamente al repositorio privado DanteDGRTX.
Se preservan todos los commits/autores y los avisos existentes. No se modifica
la visibilidad, ramas ni contenido del repositorio de origen.

No se encontró LICENSE/NOTICE general del proyecto en el historial inspeccionado;
no se inventa una licencia ni se presenta el material ajeno como una obra nueva.
Los derechos y atribuciones existentes siguen aplicándose. En particular:

- Inter: [SIL OFL 1.1 original](../web/portal/static/portal/firebase/assets/Inter-LICENSE.txt)
  y [procedencia de la copia](../web/portal/static/portal/firebase/assets/README.md).
- Bootstrap 5.3.8: banner de copyright/licencia MIT conservado en el CSS y
  [aviso y enlaces originales](../web/portal/static/portal/vendor/README.md).
- Marcas Dispensalud/TECSUP y producto: avisos de titulares en los recursos. La
  visibilidad privada no concede una licencia abierta sobre ellos.

## Pendientes

Hardware real y pruebas físicas de vinculación/batería/stock/dispensación, IA/OCR,
notificaciones persistentes y publicación Play Store con firma de distribución,
privacidad y requisitos de tienda. El APK actual es un prototipo debug; los
registros manuales no acreditan dispensación ni ingestión medidas por hardware.
