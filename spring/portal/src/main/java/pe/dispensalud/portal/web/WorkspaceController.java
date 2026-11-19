package pe.dispensalud.portal.web;

import jakarta.validation.Valid;
import java.time.Instant;
import java.util.Map;
import org.springframework.http.*;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;
import jakarta.servlet.http.HttpServletResponse;
import pe.dispensalud.core.*;
import pe.dispensalud.core.CareData.*;

@Controller
public class WorkspaceController {
    private final PatientService patients; private final SupervisionPort supervision;
    public WorkspaceController(PatientService patients, SupervisionPort supervision) {
        this.patients=patients; this.supervision=supervision;
    }
    @GetMapping("/health") @ResponseBody
    public Map<String,String> health() { return Map.of("status","ok","service","dispensalud-management"); }

    @GetMapping("/workspace")
    public String workspace(@AuthenticationPrincipal Jwt jwt, Model model) {
        return view(jwt,model,PatientForm.empty(),"",null);
    }
    @PostMapping("/patients")
    public String save(@AuthenticationPrincipal Jwt jwt, @Valid @ModelAttribute("draft") PatientForm form,
            BindingResult errors, Model model, HttpServletResponse response) {
        if (errors.hasErrors()) {
            response.setStatus(422);
            model.addAttribute("error","Revisa los campos: nombre, edad de 0 a 130 y contacto de emergencia son obligatorios.");
            return view(jwt,model,form,"",null);
        }
        try {
            patients.save(jwt.getSubject(),form.id(),form.patient(),form.version());
            return view(jwt,model,PatientForm.empty(),"Paciente guardado y confirmado por Firebase.",null);
        } catch (CareFailure failure) {
            response.setStatus(failure.kind()==CareFailure.Kind.CONFLICT ? 409 : 503);
            model.addAttribute("error",failure.getMessage());
            return view(jwt,model,form,"",null);
        }
    }
    @PostMapping("/patients/delete")
    public String remove(@AuthenticationPrincipal Jwt jwt, @RequestParam String id, @RequestParam long revision,
            @RequestParam String mutationId, Model model, HttpServletResponse response) {
        String notice="";
        try { patients.remove(jwt.getSubject(),id,new Version(revision,mutationId)); notice="Paciente dado de baja. La sincronización conserva su referencia."; }
        catch (CareFailure failure) { response.setStatus(409); model.addAttribute("error",failure.getMessage()); }
        return view(jwt,model,PatientForm.empty(),notice,null);
    }
    @PostMapping("/supervision")
    public String inspect(@AuthenticationPrincipal Jwt jwt, Model model, HttpServletResponse response) {
        Report report=null;
        try { report=supervision.inspect(new Inspection(patients.list(jwt.getSubject()).doses(),Instant.now())); }
        catch (CareFailure | IllegalArgumentException failure) { response.setStatus(503); model.addAttribute("error",failure.getMessage()); }
        return view(jwt,model,PatientForm.empty(),"",report);
    }
    private String view(Jwt jwt, Model model, PatientForm draft, String notice, Report report) {
        Snapshot snapshot=patients.list(jwt.getSubject());
        model.addAttribute("patients",snapshot.patients().stream().map(PatientForm::from).toList());
        model.addAttribute("treatmentCount",snapshot.treatments().size());
        model.addAttribute("draft",draft); model.addAttribute("notice",notice); model.addAttribute("report",report);
        return "workspace :: content";
    }
}
