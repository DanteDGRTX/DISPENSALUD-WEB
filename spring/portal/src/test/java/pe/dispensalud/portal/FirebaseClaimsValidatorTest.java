package pe.dispensalud.portal;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;
import org.springframework.http.MediaType;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.*;
import pe.dispensalud.portal.security.FirebaseClaimsValidator;
import java.time.Instant;
import java.util.List;

class FirebaseClaimsValidatorTest {
    Jwt token(boolean verified){
        Instant now=Instant.now();
        return Jwt.withTokenValue("test-token").header("alg","RS256").subject("accountA").audience(List.of("test-project"))
            .issuedAt(now.minusSeconds(10)).expiresAt(now.plusSeconds(3500))
            .claim("auth_time",now.minusSeconds(10).getEpochSecond()).claim("email_verified",verified).build();
    }
    @Test void unverifiedAccountDoesNotReachIdentityServer(){
        var builder=RestClient.builder();var remote=MockRestServiceServer.bindTo(builder).build();
        assertTrue(new FirebaseClaimsValidator("test-project","public-test-key",builder.build()).validate(token(false)).hasErrors());
        remote.verify();
    }
    @Test void accountRevocationRejectsOtherwiseValidClaims(){
        var builder=RestClient.builder();var remote=MockRestServiceServer.bindTo(builder).build();
        remote.expect(anything()).andRespond(withSuccess("{\"users\":[{\"localId\":\"accountA\",\"emailVerified\":true,\"validSince\":\"9999999999\"}]}",MediaType.APPLICATION_JSON));
        assertTrue(new FirebaseClaimsValidator("test-project","public-test-key",builder.build()).validate(token(true)).hasErrors());remote.verify();
    }
}
