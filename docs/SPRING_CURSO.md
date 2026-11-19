# Desarrollo de Aplicaciones Web: integración Spring de Dispensalud

## Alcance implementado

La web Django/Firebase incorpora una sección **Gestión de pacientes** cuando se inicia con la integración Spring. El navegador usa su token Firebase actual, Django reenvía únicamente rutas permitidas a un servicio loopback y Spring Security verifica firma, emisor, audiencia, correo y vigencia de la cuenta. No se crea un segundo registro de usuarios.

Spring MVC renderiza formularios y listas mediante Thymeleaf. Permite crear, editar y dar de baja lógicamente pacientes sin tratamientos/historial conocido. Conserva el contrato Firestore v1: ownerUid, revision, mutationId, deleted, updatedAt de servidor y body.foto=null. Las fotos, los tratamientos y la planificación actual siguen en sus circuitos existentes. No se reescriben reglas Firebase ni Android.

Un segundo servicio Spring ejecuta una revisión por agentes reactivos deterministas. Detecta pendientes vencidas y ocurrencias repetidas, comunica observaciones al coordinador y devuelve un informe. No utiliza modelos de IA, no envía correos y no escribe resultados ni alertas clínicas.

## Relación con los criterios

| Criterio | Evidencia ejecutable |
|---|---|
| Idea | Organización de pacientes y seguimiento administrativo de registros de medicación |
| MVC | WorkspaceController, PatientForm y templates/workspace.html; formulario real atendido por Java |
| N-Capas | Presentación MVC; aplicación PatientService; dominio Patient/CareData; infraestructura |
| Hexagonal | core no depende de Spring; puertos CareRepository/SupervisionPort y adaptadores FirestoreRepository/SupervisionHttpAdapter |
| Microservicios | portal y supervision son JAR independientes con puertos/arranque propios y contrato HTTP autenticado |
| Agentes | PendingAgent y DuplicateAgent tienen objetivo y percepción; Mailbox transmite mensajes al coordinador; cada ejecución produce trazabilidad e informe |
| Conocimiento Spring Boot | Autoconfiguración, beans, inyección por constructor, Spring MVC, Thymeleaf, Validation, Security resource server, RestClient y pruebas |

Son dos servicios con responsabilidades acotadas, no un rediseño completo de todo Dispensalud como microservicios. La programación de agentes implementada es reactiva y basada en reglas: no equivale a JADE, BDI ni agentes LLM. Si el curso exige uno de esos marcos, se requiere una adaptación específica.

## Estructura

- spring/core: dominio y casos de uso Java sin dependencias de Spring.
- spring/portal: servicio MVC, seguridad Firebase, repositorio Firestore y cliente HTTP de supervisión.
- spring/supervision: servicio de agentes con autenticación interna.
- web/portal/spring_proxy.py: proxy de rutas fijas, sin cookies ni redirecciones.
- web/frontend/spring.js: formularios autenticados, conservación de borradores y cancelación por cuenta.
- scripts/Start-Course.ps1 y scripts/start-course.sh: arranque coordinado.
- .github/workflows/spring-course.yml: verificación Java, Django y build frontend.

La carpeta api/ mantiene la implementación SQL histórica. No se inicia junto con estos servicios y sus cuentas no se mezclan con Firebase.

## Iniciar en Windows con Codex/IntelliJ

Requisitos: JDK 17 o posterior, Maven 3.6.3 o posterior, Python compatible con web/requirements.txt, Node 22+ y acceso a los registros de dependencias.

Desde la raíz:

    .\scripts\Start-Course.ps1

El script ejecuta las pruebas Maven, prepara dos JAR, genera una clave interna efímera en el entorno de los procesos, inicia ambos servicios y ejecuta Start-Web.ps1 para preparar/compilar la web. No imprime ni escribe la clave. Rechaza puertos ocupados y al terminar solo cierra los procesos que inició.

Abrir http://localhost:8000, ingresar con una cuenta Firebase verificada y elegir **Gestión de pacientes**. Para demostrar escrituras usar registros ficticios identificables de la propia cuenta. Son escrituras reales a esa cuenta Firebase; no existe una importación automática ni modo demo que fabrique éxito.

Si se ejecuta solo Start-Web.ps1 sin DISPENSALUD_SPRING_URL, la sección adicional no se muestra. Los demás flujos siguen usando Firebase.

Linux:

    bash scripts/start-course.sh

No iniciar ese script encima del servidor publicado ni sobre puertos ajenos. Es un arranque de desarrollo en loopback.

## Ejecutar desde IntelliJ

Importar spring/pom.xml como proyecto Maven. Ejecutar primero SupervisionApplication y después PortalApplication, con la misma variable DISPENSALUD_SUPERVISION_TOKEN de al menos 32 caracteres en ambos procesos. Configurar en Django DISPENSALUD_SPRING_URL=http://127.0.0.1:8091.

Puertos predeterminados:
- Django: 8000.
- Gestión: 8091, loopback.
- Supervisión: 8092, loopback.

No poner tokens Firebase en variables compartidas, URLs, código o capturas. El navegador obtiene cada token mediante el SDK y lo envía por Authorization.

## Pruebas

    mvn -B -f spring/pom.xml verify
    cd web
    npm ci
    npm test
    npm run build
    python manage.py test portal

Las pruebas Java usan puertos sustituidos/mocks y cuentas ficticias; no acceden al Firebase real. Cubren borradores obsoletos, baja lógica y conservación de historial, agentes, formularios MVC, ausencia de autenticación, escape HTML, revocación y precondiciones del commit Firestore. Las pruebas Django cubren rutas del proxy, token, origen, tamaño y rechazo de redirecciones/cookies.

El build frontend es obligatorio después de cambiar frontend/. Los scripts de desarrollo lo ejecutan. No basta copiar main.js sobre AWS: el navegador carga el bundle compilado.

## Recorrido para exponer, aproximadamente ocho minutos

1. Idea y límite del producto: organizar registros; diferenciar registro manual de entrega física.
2. Iniciar los dos servicios y la web; mostrar los nombres y puertos en las terminales.
3. Ingresar, abrir Gestión de pacientes, registrar FICTICIO y editar sus notas.
4. Mostrar WorkspaceController, PatientService, CareRepository y FirestoreRepository; seguir una solicitud completa.
5. Enviar una edad inválida y comprobar que no se guarda. Explicar revision/mutationId y mostrar las pruebas de edición concurrente.
6. Ejecutar Revisar registros. Mostrar PendingAgent, DuplicateAgent, Mailbox y las pruebas con dosis ficticias. El panel real puede estar sin observaciones: no inventarlas.
7. Detener únicamente supervision y repetir la revisión: falla ese informe, pero la gestión de pacientes sigue operando. Reiniciarlo para cerrar la demostración.
8. Ejecutar Maven verify y explicar qué comprueba cada prueba.

Mensaje propuesto: “La interfaz MVC delega los casos de uso en servicios. El dominio depende de puertos y los adaptadores conectan con Firebase y con el servicio de supervisión. Cada servicio puede arrancarse por separado; los agentes producen observaciones trazables sin cambiar resultados clínicos.”

## Publicación posterior

Esta integración necesita dos procesos Java adicionales. No está desplegada por crear el commit o abrir el PR.

Conservar Django, Firebase y shared/private-photos. Provisionar servicios independientes en loopback, una clave interna persistente fuera de Git y límites de memoria adecuados antes de habilitar DISPENSALUD_SPRING_URL. No utilizar automáticamente la unidad antigua Docker/Spring SQL. La receta de release anterior no incluye los nuevos JAR ni su operación; esta ampliación requiere un paquete y una validación de despliegue específicos.

El frontend compilado también debe corresponder a estas fuentes. La web publicada permanece en la versión anterior hasta una publicación explícita.

## Límites conocidos

- Las operaciones nuevas de negocio se centran en pacientes; tratamientos y fotos continúan en la implementación vigente.
- La revisión no es un servicio de notificaciones persistentes ni supervisa cuando nadie la solicita.
- El servicio consulta colecciones propias con paginación interna y un máximo de 5000 documentos por colección. La revisión admite 5000 dosis.
- La baja comprueba tratamientos/historial en el estado leído y conserva un tombstone. No promete un bloqueo distribuido global de todos los clientes.
- Solo se admite el proyecto Firebase real configurado; los tokens sin firma de emulador no se aceptan en Java.
- Las consultas Firestore siguen sujetas a reglas y cuotas publicadas.

