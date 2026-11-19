package pe.dispensalud.portal.security;

import java.time.Instant;
import java.util.*;
import org.springframework.security.oauth2.core.*;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.client.RestClient;

public final class FirebaseClaimsValidator implements OAuth2TokenValidator<Jwt> {
    private final String project, key;
    private final RestClient client;
    public FirebaseClaimsValidator(String project, String key, RestClient client) {
        this.project = project; this.key = key; this.client = client;
    }
    public OAuth2TokenValidatorResult validate(Jwt jwt) {
        try {
            Instant now = Instant.now();
            Number authTime = jwt.getClaim("auth_time");
            String uid = jwt.getSubject();
            if (uid == null || !uid.matches("[A-Za-z0-9][A-Za-z0-9_-]{0,127}") ||
                !jwt.getAudience().equals(List.of(project)) || !Boolean.TRUE.equals(jwt.getClaim("email_verified")) ||
                jwt.getIssuedAt() == null || jwt.getExpiresAt() == null ||
                !jwt.getExpiresAt().isAfter(now) || jwt.getIssuedAt().isAfter(now.plusSeconds(30)) ||
                jwt.getExpiresAt().getEpochSecond() - jwt.getIssuedAt().getEpochSecond() > 3700 ||
                authTime == null || authTime.doubleValue() != authTime.longValue() ||
                authTime.longValue() > now.getEpochSecond() + 30) return denied();
            Map<?,?> result = client.post().uri("https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={key}", key)
                .body(Map.of("idToken", jwt.getTokenValue())).retrieve().body(Map.class);
            if (result == null || !(result.get("users") instanceof List<?> users) || users.size() != 1 ||
                !(users.get(0) instanceof Map<?,?> account) || !uid.equals(account.get("localId")) ||
                !Boolean.TRUE.equals(account.get("emailVerified")) || Boolean.TRUE.equals(account.get("disabled"))) return denied();
            long validSince = Long.parseLong(String.valueOf(account.containsKey("validSince") ? account.get("validSince") : "0"));
            return validSince <= authTime.longValue() ? OAuth2TokenValidatorResult.success() : denied();
        } catch (Exception ignored) { return denied(); }
    }
    private OAuth2TokenValidatorResult denied() {
        return OAuth2TokenValidatorResult.failure(new OAuth2Error("invalid_token", "Sesión no válida o no verificada.", null));
    }
}
