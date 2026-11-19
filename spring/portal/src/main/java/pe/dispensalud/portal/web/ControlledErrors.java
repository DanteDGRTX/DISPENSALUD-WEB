package pe.dispensalud.portal.web;

import java.util.Map;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import pe.dispensalud.core.CareFailure;

@RestControllerAdvice
public class ControlledErrors {
    @ExceptionHandler(CareFailure.class)
    ResponseEntity<?> care(CareFailure failure) {
        int status=switch(failure.kind()) { case CONFLICT -> 409; case NOT_FOUND -> 404; case FORBIDDEN -> 403; case LIMIT -> 422; default -> 503; };
        return ResponseEntity.status(status).body(Map.of("error",failure.getMessage()));
    }
    @ExceptionHandler(IllegalArgumentException.class)
    ResponseEntity<?> invalid(IllegalArgumentException failure) {
        return ResponseEntity.badRequest().body(Map.of("error","Revisa los datos enviados."));
    }
}
