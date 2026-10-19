# Portal Django con Bootstrap

El cuidador puede consultar a sus personas vinculadas, registrar medicamentos y crear horarios diarios. La persona mayor recibe una vista legible y sencilla de su programación. Ambas vistas son adaptables a móviles.

Django renderiza el portal, valida formularios y protege los POST con CSRF. Consulta la API desde el servidor y guarda el token en una sesión del servidor. Los datos de negocio pertenecen a Spring Boot; Django no modifica sus tablas directamente.

Usa `scripts/Start-Web.ps1` desde la raíz para preparar el entorno y arrancar Django. `DISPENSALUD_API_URL` define el servidor de API; por defecto es `http://127.0.0.1:8080/api/v1`. En desarrollo se crea una clave aleatoria local en `data/`, ignorada por Git. Con `DJANGO_DEBUG=0` se exige `DJANGO_SECRET_KEY`; el despliegue público también requiere configurar TLS y el almacenamiento apropiado de sesiones.
