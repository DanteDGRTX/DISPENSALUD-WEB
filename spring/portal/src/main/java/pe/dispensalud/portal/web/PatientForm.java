package pe.dispensalud.portal.web;

import jakarta.validation.constraints.*;
import pe.dispensalud.core.Patient;
import pe.dispensalud.core.CareData.*;

public record PatientForm(
    String id, long revision, String mutationId,
    @NotBlank @Size(max=120) String nombre,
    @Min(0) @Max(130) int edad,
    @NotNull @Size(max=4000) String notas,
    @NotBlank @Size(max=200) String contactoEmergencia
) {
    public PatientForm { id = id == null ? "" : id; mutationId = mutationId == null ? "" : mutationId; }
    public static PatientForm empty() { return new PatientForm("",0,"","",0,"",""); }
    public static PatientForm from(PatientRecord p) {
        return new PatientForm(p.id(),p.version().revision(),p.version().mutationId(),p.body().nombre(),
            p.body().edad(),p.body().notas(),p.body().contactoEmergencia());
    }
    public Patient patient() { return new Patient(nombre,edad,notas,contactoEmergencia); }
    public Version version() { return new Version(revision,mutationId); }
}
