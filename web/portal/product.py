PRODUCT_PARTS = [
    {"number": "01", "name": "Tapa transparente", "detail": "Cubierta propuesta para inspeccionar el carrusel sin abrir cada compartimento."},
    {"number": "02", "name": "Carrusel giratorio", "detail": "Organización física de las dosis. La integración y validación del mecanismo están pendientes."},
    {"number": "03", "name": "Pantalla y controles", "detail": "Interfaz local prevista para consultar el horario y acompañar los avisos del dispositivo."},
    {"number": "04", "name": "Salida por gravedad", "detail": "Canal de entrega contemplado en el diseño; requiere pruebas mecánicas y sensores."},
]
PRODUCT_SPECS = [
    {"name": "Portal de cuidado", "detail": "Cuentas separadas, medicamentos, horarios, historial y solicitudes de ayuda.", "status": "Disponible"},
    {"name": "Información compartida", "detail": "API Java y PostgreSQL externo; acceso autorizado por vínculo entre cuidador y persona.", "status": "Disponible"},
    {"name": "Diseño físico", "detail": "Carrusel, tapa, controles y salida representados en el material visual del equipo.", "status": "Prototipo de diseño"},
    {"name": "ESP32 y trabajo sin Internet", "detail": "Plan local vigente, reloj confiable y sincronización sin dispensaciones duplicadas.", "status": "Pendiente de integración"},
    {"name": "Aplicación Android", "detail": "Cliente Kotlin y avisos al cuidador utilizando la misma lógica de negocio.", "status": "Planificado"},
    {"name": "Energía y sensores", "detail": "Respaldo de energía, detección de atascos y pruebas de dispensación.", "status": "Pendiente de validación"},
]
GALLERY = [
    {"file": "detalle-producto.jpg", "name": "Diseño del producto", "caption": "Compartimentos y carrusel del concepto presentado por el equipo."},
    {"file": "diseno-tecnico.jpg", "name": "Arquitectura del prototipo", "caption": "Referencia visual de los componentes propuestos."},
    {"file": "cuidado-hogar.jpg", "name": "Cuidado en casa", "caption": "Una experiencia para acompañar a la persona y su cuidador."},
]
