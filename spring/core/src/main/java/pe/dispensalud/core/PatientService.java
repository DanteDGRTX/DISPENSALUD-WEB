package pe.dispensalud.core;

import java.util.UUID;
import pe.dispensalud.core.CareData.*;
import static pe.dispensalud.core.CareFailure.Kind.*;

public final class PatientService {
    private final CareRepository repository;
    public PatientService(CareRepository repository) { this.repository = repository; }
    public Snapshot list(String uid) { return repository.snapshot(uid); }
    public void save(String uid, String id, Patient patient, Version expected) {
        if (id == null || id.isBlank()) {
            repository.writePatient(uid, UUID.randomUUID().toString(), patient, null, false);
        } else {
            PatientRecord current = current(uid, id, expected);
            repository.writePatient(uid, id, patient, current, false);
        }
    }
    public void remove(String uid, String id, Version expected) {
        PatientRecord current = current(uid, id, expected);
        Snapshot data = repository.snapshot(uid);
        if (data.treatments().stream().anyMatch(t -> t.patientId().equals(id)) ||
            data.doses().stream().anyMatch(d -> d.patientId().equals(id)))
            throw new CareFailure(CONFLICT, "El paciente tiene tratamientos o historial. Conserva sus datos; no se ha eliminado.");
        repository.writePatient(uid, id, current.body(), current, true);
    }
    private PatientRecord current(String uid, String id, Version expected) {
        if (!id.matches("[A-Za-z0-9][A-Za-z0-9_-]{0,127}") || id.toLowerCase().startsWith("demo-"))
            throw new IllegalArgumentException("Identificador inválido.");
        PatientRecord current = repository.findPatient(uid, id);
        if (current == null || current.deleted()) throw new CareFailure(NOT_FOUND, "Paciente no disponible.");
        if (expected == null || !current.version().equals(expected))
            throw new CareFailure(CONFLICT, "Otro dispositivo cambió el paciente. Actualiza y revisa antes de guardar.");
        return current;
    }
}
