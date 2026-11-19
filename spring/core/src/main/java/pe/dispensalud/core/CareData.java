package pe.dispensalud.core;

import java.time.Instant;
import java.util.List;

public final class CareData {
    private CareData() {}
    public record Version(long revision, String mutationId) {}
    public record PatientRecord(String id, Patient body, Version version, String updateTime, boolean deleted) {}
    public record Treatment(String id, String patientId, boolean active) {}
    public record Dose(String id, String patientId, String treatmentId, long scheduledAt, String state) {}
    public record Snapshot(List<PatientRecord> patients, List<Treatment> treatments, List<Dose> doses) {
        public Snapshot {
            patients = List.copyOf(patients); treatments = List.copyOf(treatments); doses = List.copyOf(doses);
        }
    }
    public record Inspection(List<Dose> doses, Instant now) {
        public Inspection {
            if (doses == null || doses.size() > 5000 || now == null) throw new IllegalArgumentException("Inspección inválida.");
            doses = List.copyOf(doses);
            for (Dose d : doses)
                if (d == null || d.id() == null || d.id().length() > 128 ||
                    d.patientId() == null || d.treatmentId() == null ||
                    !List.of("PENDING","TAKEN","LATE","MISSED").contains(d.state()))
                    throw new IllegalArgumentException("Dosis incompatible.");
        }
    }
    public record Message(String sender, String recipient, String kind, String reference) {}
    public record Finding(String kind, String reference, String description) {}
    public record Report(String runId, String state, List<Finding> findings, List<Message> trace) {}
}
