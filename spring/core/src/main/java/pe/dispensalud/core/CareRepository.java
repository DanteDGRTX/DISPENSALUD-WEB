package pe.dispensalud.core;

import pe.dispensalud.core.CareData.*;

public interface CareRepository {
    Snapshot snapshot(String ownerUid);
    PatientRecord findPatient(String ownerUid, String id);
    void writePatient(String ownerUid, String id, Patient body, PatientRecord expected, boolean deleted);
}
