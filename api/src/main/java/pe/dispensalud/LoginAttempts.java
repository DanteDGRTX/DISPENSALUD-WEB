package pe.dispensalud;

import java.sql.Timestamp;
import java.time.Instant;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

@Service
public class LoginAttempts {
    private final JdbcTemplate database;

    public LoginAttempts(JdbcTemplate database) {
        this.database = database;
    }

    public void record(String identityHash) {
        Instant now = Instant.now();
        database.update("DELETE FROM login_attempts WHERE expires_at <= ?", Timestamp.from(now));
        try {
            database.update("INSERT INTO login_attempts(identity_hash, attempts, expires_at) VALUES (?, 1, ?)",
                identityHash, Timestamp.from(now.plusSeconds(900)));
            return;
        } catch (DuplicateKeyException exception) {
            int changed = database.update("UPDATE login_attempts SET attempts = attempts + 1 "
                + "WHERE identity_hash = ? AND attempts < 5 AND expires_at > ?", identityHash, Timestamp.from(now));
            if (changed == 0) {
                throw new ResponseStatusException(HttpStatus.TOO_MANY_REQUESTS,
                    "Demasiados intentos. Espera 15 minutos antes de volver a ingresar.");
            }
        }
    }

    public void clear(String identityHash) {
        database.update("DELETE FROM login_attempts WHERE identity_hash = ?", identityHash);
    }
}
