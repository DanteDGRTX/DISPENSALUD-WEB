package pe.dispensalud.supervision;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import org.springframework.http.MediaType;

@SpringBootTest(properties={"dispensalud.supervision.token=test-only-shared-token-01234567890123456789"})
@AutoConfigureMockMvc
class InspectionTest {
    @Autowired MockMvc mvc;
    @Test void internalEndpointRequiresServiceIdentity() throws Exception {
        mvc.perform(post("/inspect").contentType(MediaType.APPLICATION_JSON).content("{}")).andExpect(status().isUnauthorized());
    }
    @Test void independentServiceReturnsAgentReport() throws Exception {
        mvc.perform(post("/inspect").header("Authorization","Bearer test-only-shared-token-01234567890123456789")
            .contentType(MediaType.APPLICATION_JSON).content("{\"doses\":[],\"now\":\"2026-11-19T12:00:00Z\"}"))
            .andExpect(status().isOk()).andExpect(jsonPath("$.state").value("COMPLETED"))
            .andExpect(jsonPath("$.trace.length()").value(4));
    }
}
