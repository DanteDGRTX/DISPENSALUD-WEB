package pe.dispensalud.portal.security;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.oauth2.core.DelegatingOAuth2TokenValidator;
import org.springframework.security.oauth2.jwt.*;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.web.client.RestClient;

@Configuration
public class SecurityConfig {
    @Bean JwtDecoder jwtDecoder(@Value("${dispensalud.firebase.project}") String project,
            @Value("${dispensalud.firebase.api-key}") String key, RestClient client) {
        NimbusJwtDecoder decoder = NimbusJwtDecoder.withJwkSetUri(
            "https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com").build();
        decoder.setJwtValidator(new DelegatingOAuth2TokenValidator<>(
            JwtValidators.createDefaultWithIssuer("https://securetoken.google.com/" + project),
            new FirebaseClaimsValidator(project, key, client)));
        return decoder;
    }
    @Bean SecurityFilterChain security(HttpSecurity http) throws Exception {
        return http.csrf(csrf -> csrf.disable())
            .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth.requestMatchers("/health").permitAll().anyRequest().authenticated())
            .oauth2ResourceServer(resource -> resource.jwt(jwt -> {}))
            .headers(headers -> headers.cacheControl(cache -> {}))
            .build();
    }
}
