package pe.dispensalud.core.agents;

import java.util.*;
import pe.dispensalud.core.CareData.*;

/** Goal-oriented deterministic reflex agents. No LLM, clinical decisions or writes. */
public final class AgentSystem {
    public interface Agent {
        String name();
        String goal();
        void perceive(Inspection world, Mailbox mailbox);
    }
    public static final class Mailbox {
        private final List<Message> messages = new ArrayList<>();
        public void send(String sender, String recipient, String kind, String reference) {
            messages.add(new Message(sender, recipient, kind, reference));
        }
        public List<Message> forAgent(String name) {
            return messages.stream().filter(m -> m.recipient().equals(name)).toList();
        }
        public List<Message> trace() { return List.copyOf(messages); }
    }
    public static final class PendingAgent implements Agent {
        public String name() { return "pending"; }
        public String goal() { return "Identify overdue pending records without changing dose outcomes"; }
        public void perceive(Inspection world, Mailbox mailbox) {
            for (Dose dose : world.doses())
                if (dose.state().equals("PENDING") && dose.scheduledAt() < world.now().toEpochMilli())
                    mailbox.send(name(), "coordinator", "OVERDUE", dose.id());
        }
    }
    public static final class DuplicateAgent implements Agent {
        public String name() { return "duplicates"; }
        public String goal() { return "Identify repeated treatment occurrences without deleting records"; }
        public void perceive(Inspection world, Mailbox mailbox) {
            Set<String> seen = new HashSet<>();
            for (Dose dose : world.doses())
                if (!seen.add(dose.treatmentId() + "|" + dose.scheduledAt()))
                    mailbox.send(name(), "coordinator", "DUPLICATE", dose.id());
        }
    }
    public Report inspect(Inspection world) {
        Mailbox mailbox = new Mailbox();
        List<Agent> agents = List.of(new PendingAgent(), new DuplicateAgent());
        for (Agent agent : agents) {
            mailbox.send("coordinator", agent.name(), "OBSERVE", agent.goal());
            agent.perceive(world, mailbox);
            mailbox.send(agent.name(), "coordinator", "DONE", agent.name());
        }
        List<Finding> findings = mailbox.forAgent("coordinator").stream()
            .filter(m -> !m.kind().equals("DONE"))
            .map(m -> new Finding(m.kind(), m.reference(), m.kind().equals("OVERDUE")
                ? "Horario vencido con registro pendiente; no confirma una omisión."
                : "Más de un registro para el mismo tratamiento y horario; requiere revisión."))
            .toList();
        return new Report(UUID.randomUUID().toString(), "COMPLETED", findings, mailbox.trace());
    }
}
