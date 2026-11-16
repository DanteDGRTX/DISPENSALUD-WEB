# Fotos privadas y recursos del servicio existente

Consultar `FOTOS_PRIVADAS_CONTRATO.md` incluido en este paquete. La identidad es
el ID token Firebase verificado por firma y consulta accounts:lookup. La propiedad
del paciente se verifica con Firestore REST y el MISMO token, bajo las reglas
actuales. No se instalan Firebase Admin, Storage, Blaze ni cuentas de servicio.

El archivo web.env no debe cambiar la clave Django existente. Puede configurar
`FIREBASE_WEB_API_KEY` con una API key pública del mismo proyecto autorizada para
Identity Toolkit desde el servidor. Si la key actual tiene restricciones solo de
referrer de navegador, revisar su uso backend antes de desplegar: no se eliminan
restricciones ni se crean credenciales automáticamente. Las comprobaciones de
cuenta/propiedad fallan cerradas si Google no está disponible.

Persistencia: `/srv/dispensalud-web/shared/private-photos/`, SQLite propio y JPEG
privados por hash UID. El servicio conserva permiso de escritura SOLO bajo shared;
la release y estáticos siguen de solo lectura. Nunca añadir alias Nginx para fotos.
La API entrega bytes solo después de autorizar. El vhost nuevo preparado admite
2 MiB de cuerpo; trasladar ese límite únicamente al bloque www al migrar.

Se añaden Pillow/PyJWT/cryptography/cffi/pycparser fijados. Se incluyen wheels
nativos para CPython 3.14 Linux x86_64 y aarch64, más wheels universales. pip elige
la arquitectura compatible; no se compila en el servidor. Se conserva un worker
y MemoryMax 192 MiB. Las imágenes de entrada se limitan antes de decodificar;
hay cuotas de 8 MiB/UID y 128 MiB global. Esto no sustituye medir la RAM real.

Tras autorización, verificar Gunicorn/Pillow/cripto en Ubuntu/Python 3.14.4. No se
ha ejecutado ese runtime remoto. Para huérfanos, primero dry-run:

```bash
sudo bash ops/manage-production.sh photo_gc
# Solo después de revisar: elimina hasta 100 huérfanos de más de una hora.
sudo bash ops/manage-production.sh photo_gc --apply
```

Respaldo/restauración del directorio privado requiere copia consistente junto al
SQLite, permisos privados y parada de SOLO dispensalud-web.service si se usa tar.
No incluir fotos en backups públicos, ZIP de código ni logs. Actualizar/revertir
la release conserva shared y la clave. Una release antigua sin esta API no verá
las fotos, pero NO debe borrar el directorio; volver a la nueva recupera referencias.

Las fotos locales antiguas Android se conservan por separado. Los clientes nuevos
solo suben cuando la persona pulsa la acción; no se hace una migración masiva.
Una referencia compartida es opaca, no una URL ni base64 en Firestore; por ello
no se cambian reglas publicadas ni el esquema patients.body.foto=null.
