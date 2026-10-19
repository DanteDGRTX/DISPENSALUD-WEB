# Firmware ESP32 — fase posterior

El firmware se añadirá después de modelar el mecanismo. El dispositivo debe autenticar su identidad, almacenar un plan firmado/versionado con vencimiento, poder registrar eventos sin conexión y evitar repetir una ocurrencia cuyo estado quedó incierto tras un reinicio.

El límite de tiempo sin Internet, los sensores disponibles, el reloj de respaldo y el comportamiento ante atasco o batería baja siguen pendientes. No se habilitará la dispensación autónoma sin probar esos escenarios con el hardware.
