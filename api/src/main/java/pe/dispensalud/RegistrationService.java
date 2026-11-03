package pe.dispensalud;

import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class RegistrationService {
    private final JdbcTemplate database;
    private final AuthService auth;
    private final boolean enabled;

    public RegistrationService(JdbcTemplate database, AuthService auth,
            @Value("${dispensalud.registration.enabled:false}") boolean enabled) {
        this.database = database;
        this.auth = auth;
        this.enabled = enabled;
    }

    @Transactional
    public Account register(String username, String displayName, String role, String password) {
        if (!enabled) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "El registro no está habilitado en este entorno.");
        }
        String canonical = username.strip().toLowerCase(Locale.ROOT);
        if (!canonical.matches("[a-z0-9._-]{4,40}") || displayName.strip().isEmpty()
                || displayName.strip().length() > 120 || password.length() < 12 || password.length() > 60
                || password.getBytes(StandardCharsets.UTF_8).length > 72
                || !("CAREGIVER".equals(role) || "OLDER_ADULT".equals(role))) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Revisa los datos de la cuenta y usa una contraseña de al menos 12 caracteres.");
        }
        UUID accountId = UUID.randomUUID();
        database.update("INSERT INTO accounts(id, username, password_hash, display_name, role) VALUES (?, ?, ?, ?, ?)",
            accountId, canonical, auth.encodePassword(password), displayName.strip(), role);
        return new Account(accountId, canonical, displayName.strip(), role);
    }
}
