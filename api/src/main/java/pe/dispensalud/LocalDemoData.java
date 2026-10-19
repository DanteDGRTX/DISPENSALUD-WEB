package pe.dispensalud;

import java.sql.Date;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.UUID;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.core.env.Environment;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Component
@Profile({"local", "demo"})
public class LocalDemoData implements CommandLineRunner {
    private final JdbcTemplate database;
    private final AuthService auth;
    private final Environment environment;

    public LocalDemoData(JdbcTemplate database, AuthService auth, Environment environment) {
        this.database = database;
        this.auth = auth;
        this.environment = environment;
    }

    @Override
    @Transactional
    public void run(String... arguments) {
        if (database.queryForObject("SELECT COUNT(*) FROM accounts", Integer.class) > 0) {
            return;
        }
        String password = environment.getProperty("DISPENSALUD_DEMO_PASSWORD", "");
        if (password.length() < 12 || password.length() > 60) {
            throw new IllegalStateException("Define DISPENSALUD_DEMO_PASSWORD con 12 a 60 caracteres para crear las cuentas ficticias locales.");
        }
        UUID caregiver = UUID.randomUUID();
        UUID adult = UUID.randomUUID();
        UUID medication = UUID.randomUUID();
        database.update("INSERT INTO accounts VALUES (?, ?, ?, ?, ?)", caregiver,
            "cuidador.demo", auth.encodePassword(password), "Cuidadora de prueba", "CAREGIVER");
        database.update("INSERT INTO accounts VALUES (?, ?, ?, ?, ?)", adult,
            "usuario.demo", auth.encodePassword(password), "Elena (persona ficticia)", "OLDER_ADULT");
        database.update("INSERT INTO care_links VALUES (?, ?)", caregiver, adult);
        database.update("INSERT INTO medications(id, person_id, name, instructions) VALUES (?, ?, ?, ?)",
            medication, adult, "Ejemplo ficticio A", "Demostracion de pantalla. No corresponde a un tratamiento real.");
        database.update("INSERT INTO schedules(id, medication_id, local_time, start_date) VALUES (?, ?, ?, ?)",
            UUID.randomUUID(), medication, java.sql.Time.valueOf("09:00:00"),
            Date.valueOf(LocalDate.now(ZoneId.of("America/Lima"))));
    }
}
