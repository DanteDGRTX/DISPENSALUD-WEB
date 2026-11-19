package pe.dispensalud.core;

public record Patient(String nombre, int edad, String notas, String contactoEmergencia) {
    public Patient {
        if (nombre == null || nombre.isBlank() || nombre.length() > 120 ||
            edad < 0 || edad > 130 || notas == null || notas.length() > 4000 ||
            contactoEmergencia == null || contactoEmergencia.isBlank() || contactoEmergencia.length() > 200)
            throw new IllegalArgumentException("Revisa nombre, edad, notas y contacto de emergencia.");
        nombre = nombre.strip();
        contactoEmergencia = contactoEmergencia.strip();
    }
}
