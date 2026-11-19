package pe.dispensalud.portal;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import pe.dispensalud.core.*;

@SpringBootApplication
public class PortalApplication {
    public static void main(String[] args) { SpringApplication.run(PortalApplication.class, args); }
    @Bean PatientService patientService(CareRepository repository) { return new PatientService(repository); }
}
