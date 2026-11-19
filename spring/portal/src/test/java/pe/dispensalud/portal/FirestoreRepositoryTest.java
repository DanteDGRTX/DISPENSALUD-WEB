package pe.dispensalud.portal;
import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;
import org.springframework.test.web.client.MockRestServiceServer;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.*;
import org.springframework.http.HttpStatus;
import org.springframework.web.client.RestClient;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import pe.dispensalud.portal.adapters.FirestoreRepository;
import pe.dispensalud.core.*;
import pe.dispensalud.core.CareData.*;

class FirestoreRepositoryTest {
    RestClient.Builder builder; MockRestServiceServer remote; FirestoreRepository repository;
    @BeforeEach void setup(){
        builder=RestClient.builder();remote=MockRestServiceServer.bindTo(builder).build();
        repository=new FirestoreRepository(builder.build(),"test-project");
        Jwt token=Jwt.withTokenValue("test-token").header("alg","RS256").subject("accountA").build();
        SecurityContextHolder.getContext().setAuthentication(new JwtAuthenticationToken(token));
    }
    @AfterEach void cleanup(){SecurityContextHolder.clearContext();remote.verify();}
    @Test void commitPreservesPhotoNullVersionAndServerTimestamp(){
        remote.expect(requestTo("https://firestore.googleapis.com/v1/projects/test-project/databases/(default)/documents:commit"))
            .andExpect(header("Authorization","Bearer test-token"))
            .andExpect(jsonPath("$.writes[0].currentDocument.updateTime").value("2026-01-01T00:00:00Z"))
            .andExpect(jsonPath("$.writes[0].update.fields.revision.integerValue").value("2"))
            .andExpect(content().string(org.hamcrest.Matchers.containsString("\"foto\":{\"nullValue\":null}")))
            .andExpect(jsonPath("$.writes[0].updateTransforms[0].setToServerValue").value("REQUEST_TIME"))
            .andRespond(withSuccess("{}",org.springframework.http.MediaType.APPLICATION_JSON));
        Patient p=new Patient("FICTICIO",60,"","Contacto");
        repository.writePatient("accountA","p",p,new PatientRecord("p",p,new Version(1,"v"),"2026-01-01T00:00:00Z",false),false);
    }
    @Test void foreignAccountNeverMakesAnHttpRequest(){
        assertThrows(CareFailure.class,()->repository.findPatient("accountB","p"));
    }
    @Test void concurrentCommitIsReportedAsConflict(){
        remote.expect(anything()).andRespond(withStatus(HttpStatus.CONFLICT));
        CareFailure failure=assertThrows(CareFailure.class,()->repository.writePatient("accountA","p",new Patient("FICTICIO",60,"","Contacto"),null,false));
        assertEquals(CareFailure.Kind.CONFLICT,failure.kind());
    }
}
