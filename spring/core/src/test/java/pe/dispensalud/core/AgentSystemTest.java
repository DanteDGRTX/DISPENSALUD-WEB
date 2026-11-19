package pe.dispensalud.core;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.time.Instant;
import java.util.List;
import pe.dispensalud.core.CareData.*;
import pe.dispensalud.core.agents.AgentSystem;

class AgentSystemTest {
    @Test void agentsReportOverdueAndDuplicatesWithoutChangingFacts(){
        List<Dose> facts=List.of(new Dose("d1","p","t",100,"PENDING"),new Dose("d2","p","t",100,"TAKEN"),
            new Dose("d3","p","t",300,"PENDING"));
        Report report=new AgentSystem().inspect(new Inspection(facts,Instant.ofEpochMilli(200)));
        assertEquals("COMPLETED",report.state());assertEquals(2,report.findings().size());
        assertTrue(report.findings().stream().anyMatch(f->f.kind().equals("OVERDUE")&&f.reference().equals("d1")));
        assertTrue(report.findings().stream().anyMatch(f->f.kind().equals("DUPLICATE")));
        assertEquals(2,report.trace().stream().filter(m->m.kind().equals("DONE")).count());
        assertEquals("PENDING",facts.get(0).state());
    }
    @Test void emptyWorldCompletesAndOversizedWorldIsRejected(){
        assertTrue(new AgentSystem().inspect(new Inspection(List.of(),Instant.now())).findings().isEmpty());
        assertThrows(IllegalArgumentException.class,()->new Inspection(java.util.Collections.nCopies(5001,new Dose("d","p","t",1,"PENDING")),Instant.now()));
    }
}
