package pe.dispensalud;

import java.sql.Date;
import java.sql.Time;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.ZoneId;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class CareService {
    private final JdbcTemplate database;

    public CareService(JdbcTemplate database) {
        this.database = database;
    }

    public List<Person> people(Account actor) {
        if (!actor.isCaregiver()) {
            return List.of(new Person(actor.id(), actor.displayName()));
        }
        return database.query("SELECT a.id, a.display_name FROM accounts a JOIN care_links c ON a.id = c.person_id WHERE c.caregiver_id = ?",
            (row, number) -> new Person(row.getObject("id", UUID.class), row.getString("display_name")), actor.id());
    }

    public List<Medication> medications(Account actor, UUID personId) {
        requireAccess(actor, personId, false);
        return database.query("SELECT id, name, instructions FROM medications WHERE person_id = ? ORDER BY created_at, id",
            (row, number) -> new Medication(row.getObject("id", UUID.class), row.getString("name"), row.getString("instructions")), personId);
    }

    @Transactional
    public Medication addMedication(Account actor, UUID personId, String name, String instructions) {
        requireAccess(actor, personId, true);
        UUID medicationId = UUID.randomUUID();
        database.update("INSERT INTO medications(id, person_id, name, instructions) VALUES (?, ?, ?, ?)",
            medicationId, personId, name.strip(), instructions.strip());
        audit(actor, personId, "MEDICATION_CREATED", medicationId);
        return new Medication(medicationId, name.strip(), instructions.strip());
    }

    @Transactional
    public Map<String, UUID> addSchedule(Account actor, UUID personId, UUID medicationId,
            LocalTime time, LocalDate start, LocalDate end) {
        requireAccess(actor, personId, true);
        if (end != null && end.isBefore(start)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "La fecha final debe ser igual o posterior a la inicial.");
        }
        Integer count = database.queryForObject("SELECT COUNT(*) FROM medications WHERE id = ? AND person_id = ?",
            Integer.class, medicationId, personId);
        if (count == null || count == 0) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Medicamento no disponible.");
        }
        UUID scheduleId = UUID.randomUUID();
        database.update("INSERT INTO schedules(id, medication_id, local_time, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            scheduleId, medicationId, Time.valueOf(time), Date.valueOf(start), end == null ? null : Date.valueOf(end));
        audit(actor, personId, "SCHEDULE_CREATED", scheduleId);
        return Map.of("id", scheduleId);
    }

    public DayPlan today(Account actor, UUID personId) {
        requireAccess(actor, personId, false);
        LocalDate today = LocalDate.now(ZoneId.of("America/Lima"));
        List<PlannedDose> doses = database.query(
            "SELECT s.id, s.local_time, m.name, m.instructions FROM schedules s JOIN medications m ON s.medication_id = m.id "
                + "WHERE m.person_id = ? AND s.enabled = TRUE AND s.start_date <= ? AND (s.end_date IS NULL OR s.end_date >= ?) ORDER BY s.local_time, s.id",
            (row, number) -> new PlannedDose(row.getObject("id", UUID.class), row.getTime("local_time").toLocalTime(),
                row.getString("name"), row.getString("instructions"), "SCHEDULED"), personId, Date.valueOf(today), Date.valueOf(today));
        return new DayPlan(today, "America/Lima", doses);
    }

    @Transactional
    public Medication updateMedication(Account actor, UUID personId, UUID medicationId, String name, String instructions) {
        requireAccess(actor, personId, true);
        int changed = database.update("UPDATE medications SET name = ?, instructions = ? WHERE id = ? AND person_id = ?",
            name.strip(), instructions.strip(), medicationId, personId);
        if (changed == 0) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Medicamento no disponible.");
        }
        audit(actor, personId, "MEDICATION_UPDATED", medicationId);
        return new Medication(medicationId, name.strip(), instructions.strip());
    }

    public List<Schedule> schedules(Account actor, UUID personId) {
        requireAccess(actor, personId, false);
        return database.query("SELECT s.*, m.name FROM schedules s JOIN medications m ON m.id = s.medication_id "
                + "WHERE m.person_id = ? ORDER BY s.local_time, s.id",
            (row, number) -> new Schedule(row.getObject("id", UUID.class), row.getObject("medication_id", UUID.class),
                row.getString("name"), row.getTime("local_time").toLocalTime(), row.getDate("start_date").toLocalDate(),
                row.getDate("end_date") == null ? null : row.getDate("end_date").toLocalDate(), row.getBoolean("enabled")), personId);
    }

    @Transactional
    public Map<String, Boolean> setScheduleEnabled(Account actor, UUID personId, UUID scheduleId, boolean enabled) {
        requireAccess(actor, personId, true);
        database.queryForObject("SELECT id FROM accounts WHERE id = ? FOR UPDATE", UUID.class, personId);
        List<Boolean> states = database.query("SELECT enabled FROM schedules WHERE id = ? "
            + "AND medication_id IN (SELECT id FROM medications WHERE person_id = ?)",
            (row, number) -> row.getBoolean("enabled"), scheduleId, personId);
        if (states.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Horario no disponible.");
        }
        if (states.get(0) != enabled) {
            database.update("UPDATE schedules SET enabled = ? WHERE id = ?", enabled, scheduleId);
            audit(actor, personId, enabled ? "SCHEDULE_RESUMED" : "SCHEDULE_PAUSED", scheduleId);
        }
        return Map.of("enabled", enabled);
    }

    public List<HistoryEvent> history(Account actor, UUID personId) {
        requireAccess(actor, personId, false);
        return database.query("SELECT e.*, a.display_name, COALESCE(m.name, sm.name, '') AS object_name "
            + "FROM audit_events e JOIN accounts a ON a.id = e.actor_id LEFT JOIN medications m ON m.id = e.object_id "
            + "LEFT JOIN schedules s ON s.id = e.object_id LEFT JOIN medications sm ON sm.id = s.medication_id "
            + "WHERE e.person_id = ? ORDER BY e.occurred_at DESC, e.id LIMIT 50",
            (row, number) -> new HistoryEvent(row.getObject("id", UUID.class), row.getString("action"),
                row.getString("display_name"), row.getString("object_name"), row.getObject("occurred_at", OffsetDateTime.class)), personId);
    }

    public List<HelpRequest> helpRequests(Account actor, UUID personId) {
        requireAccess(actor, personId, false);
        return database.query("SELECT * FROM help_requests WHERE person_id = ? ORDER BY created_at DESC LIMIT 50",
            (row, number) -> new HelpRequest(row.getObject("id", UUID.class), row.getString("status"),
                row.getObject("created_at", OffsetDateTime.class)), personId);
    }

    @Transactional
    public Map<String, UUID> requestHelp(Account actor, UUID personId) {
        requireAccess(actor, personId, false);
        if (actor.isCaregiver() || !actor.id().equals(personId)) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Esta acción corresponde a la persona usuaria.");
        }
        database.queryForObject("SELECT id FROM accounts WHERE id = ? FOR UPDATE", UUID.class, personId);
        List<UUID> pending = database.query("SELECT id FROM help_requests WHERE person_id = ? AND status = 'OPEN'",
            (row, number) -> row.getObject("id", UUID.class), personId);
        if (!pending.isEmpty()) {
            return Map.of("id", pending.get(0));
        }
        UUID requestId = UUID.randomUUID();
        database.update("INSERT INTO help_requests(id, person_id) VALUES (?, ?)", requestId, personId);
        audit(actor, personId, "HELP_REQUESTED", requestId);
        return Map.of("id", requestId);
    }

    @Transactional
    public Map<String, String> resolveHelp(Account actor, UUID personId, UUID requestId) {
        requireAccess(actor, personId, true);
        int changed = database.update("UPDATE help_requests SET status = 'CLOSED', resolved_at = CURRENT_TIMESTAMP "
            + "WHERE id = ? AND person_id = ? AND status = 'OPEN'", requestId, personId);
        if (changed == 0) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "La solicitud ya fue atendida o no está disponible.");
        }
        audit(actor, personId, "HELP_RESOLVED", requestId);
        return Map.of("status", "CLOSED");
    }

    private void requireAccess(Account actor, UUID personId, boolean write) {
        boolean ownsView = actor.id().equals(personId) && !write && !actor.isCaregiver();
        Integer links = actor.isCaregiver() ? database.queryForObject(
            "SELECT COUNT(*) FROM care_links WHERE caregiver_id = ? AND person_id = ?", Integer.class, actor.id(), personId) : 0;
        if (!ownsView && (links == null || links == 0)) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tienes permiso para esta persona.");
        }
    }

    private void audit(Account actor, UUID personId, String action, UUID objectId) {
        database.update("INSERT INTO audit_events(id, actor_id, action, object_id, person_id) VALUES (?, ?, ?, ?, ?)",
            UUID.randomUUID(), actor.id(), action, objectId, personId);
    }

    public record Person(UUID id, String displayName) { }
    public record Medication(UUID id, String name, String instructions) { }
    public record PlannedDose(UUID scheduleId, LocalTime localTime, String name, String instructions, String status) { }
    public record DayPlan(LocalDate date, String timezone, List<PlannedDose> doses) { }
    public record Schedule(UUID id, UUID medicationId, String name, LocalTime localTime, LocalDate startDate, LocalDate endDate, boolean enabled) { }
    public record HistoryEvent(UUID id, String action, String actor, String objectName, OffsetDateTime occurredAt) { }
    public record HelpRequest(UUID id, String status, OffsetDateTime createdAt) { }
}
