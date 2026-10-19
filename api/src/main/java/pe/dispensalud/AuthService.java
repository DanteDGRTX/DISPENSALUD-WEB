package pe.dispensalud;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.Base64;
import java.util.HexFormat;
import java.util.List;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

@Service
public class AuthService {
    private final JdbcTemplate database;
    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();
    private final SecureRandom random = new SecureRandom();
    private final String dummyHash = encoder.encode(UUID.randomUUID().toString());

    public AuthService(JdbcTemplate database) {
        this.database = database;
    }

    public Session login(String username, String password) {
        List<Credential> matches = database.query(
            "SELECT * FROM accounts WHERE username = ?",
            (row, number) -> new Credential(new Account(row.getObject("id", UUID.class),
                row.getString("username"), row.getString("display_name"), row.getString("role")),
                row.getString("password_hash")), username);
        String storedHash = matches.isEmpty() ? dummyHash : matches.get(0).passwordHash();
        if (!encoder.matches(password, storedHash) || matches.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Credenciales incorrectas.");
        }
        byte[] bytes = new byte[32];
        random.nextBytes(bytes);
        String token = Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
        Instant expiresAt = Instant.now().plusSeconds(28800);
        database.update("DELETE FROM auth_sessions WHERE expires_at <= ?", Timestamp.from(Instant.now()));
        database.update("INSERT INTO auth_sessions(token_hash, account_id, expires_at) VALUES (?, ?, ?)",
            hash(token), matches.get(0).account().id(), Timestamp.from(expiresAt));
        return new Session(token, expiresAt, matches.get(0).account());
    }

    public Account findSession(String token) {
        if (token == null || token.length() > 128) {
            return null;
        }
        List<Account> accounts = database.query(
            "SELECT a.* FROM accounts a JOIN auth_sessions s ON a.id = s.account_id "
                + "WHERE s.token_hash = ? AND s.expires_at > ?",
            (row, number) -> new Account(row.getObject("id", UUID.class), row.getString("username"),
                row.getString("display_name"), row.getString("role")), hash(token), Timestamp.from(Instant.now()));
        return accounts.isEmpty() ? null : accounts.get(0);
    }

    public void logout(String token) {
        database.update("DELETE FROM auth_sessions WHERE token_hash = ?", hash(token));
    }

    public String encodePassword(String password) {
        return encoder.encode(password);
    }

    private String hash(String token) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                .digest(token.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException(exception);
        }
    }

    private record Credential(Account account, String passwordHash) { }
    public record Session(String token, Instant expiresAt, Account account) { }
}
