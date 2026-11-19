package pe.dispensalud.supervision;

import java.util.Map;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import pe.dispensalud.core.CareData.*;
import pe.dispensalud.core.agents.AgentSystem;

@RestController
public class InspectionController {
    private final AgentSystem agents=new AgentSystem();
    @GetMapping("/health") public Map<String,String> health() { return Map.of("status","ok","service","dispensalud-supervision"); }
    @PostMapping("/inspect") public Report inspect(@RequestBody Inspection inspection) { return agents.inspect(inspection); }
    @ExceptionHandler(IllegalArgumentException.class) public ResponseEntity<?> invalid() {
        return ResponseEntity.badRequest().body(Map.of("error","Inspección inválida."));
    }
}
