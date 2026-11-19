package pe.dispensalud.portal;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.test.web.servlet.MockMvc;
import pe.dispensalud.core.*;
import pe.dispensalud.core.CareData.*;
import java.util.List;
import static org.mockito.Mockito.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.jwt;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest(properties={"dispensalud.supervision.token=test-only-shared-token-01234567890123456789"})
@AutoConfigureMockMvc
class WorkspaceTest {
    @Autowired MockMvc mvc;
    @MockBean CareRepository repository;
    @MockBean SupervisionPort supervision;
    @MockBean JwtDecoder decoder;
    @BeforeEach void setup(){when(repository.snapshot(anyString())).thenReturn(new Snapshot(List.of(),List.of(),List.of()));}
    @Test void unauthenticatedWorkspaceIsRejected() throws Exception {
        mvc.perform(get("/workspace")).andExpect(status().isUnauthorized());verifyNoInteractions(repository);
    }
    @Test void createsPatientThroughMvcServiceAndPort() throws Exception {
        mvc.perform(post("/patients").with(jwt().jwt(j->j.subject("accountA")))
            .param("id","").param("revision","0").param("mutationId","")
            .param("nombre","FICTICIO").param("edad","60").param("notas","").param("contactoEmergencia","Contacto"))
            .andExpect(status().isOk()).andExpect(content().string(org.hamcrest.Matchers.containsString("Paciente guardado")));
        verify(repository).writePatient(eq("accountA"),anyString(),eq(new Patient("FICTICIO",60,"","Contacto")),isNull(),eq(false));
    }
    @Test void invalidFormDoesNotWriteAndPreservesDraft() throws Exception {
        mvc.perform(post("/patients").with(jwt()).param("nombre","FICTICIO").param("edad","131")
            .param("notas","").param("contactoEmergencia","Contacto").param("revision","0"))
            .andExpect(status().isUnprocessableEntity()).andExpect(content().string(org.hamcrest.Matchers.containsString("FICTICIO")));
        verify(repository,never()).writePatient(anyString(),anyString(),any(),any(),anyBoolean());
    }
    @Test void thymeleafEscapesNames() throws Exception {
        when(repository.snapshot("accountA")).thenReturn(new Snapshot(List.of(new PatientRecord("p",
            new Patient("<script>alert(1)</script>",60,"","Contacto"),new Version(1,"v"),"time",false)),List.of(),List.of()));
        mvc.perform(get("/workspace").with(jwt().jwt(j->j.subject("accountA")))).andExpect(status().isOk())
            .andExpect(content().string(org.hamcrest.Matchers.containsString("&lt;script&gt;")))
            .andExpect(content().string(org.hamcrest.Matchers.not(org.hamcrest.Matchers.containsString("<script>alert(1)</script>"))));
    }
}
