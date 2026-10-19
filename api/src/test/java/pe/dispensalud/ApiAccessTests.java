package pe.dispensalud;

import com.fasterxml.jackson.databind.JsonNode;
import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class ApiAccessTests {
    private static final UUID CAREGIVER = UUID.fromString("10000000-0000-0000-0000-000000000001");
    private static final UUID ADULT = UUID.fromString("10000000-0000-0000-0000-000000000002");
    private static final UUID OTHER_ADULT = UUID.fromString("10000000-0000-0000-0000-000000000003");
    private static final String PASSWORD = "Test-only-password-2026";

    @Autowired TestRestTemplate client;
    @Autowired JdbcTemplate database;
    @Autowired AuthService auth;

    @BeforeEach
    void prepareAccounts() {
        for (String table : new String[]{"login_attempts", "audit_events", "help_requests", "schedules", "medications", "auth_sessions", "care_links", "accounts"}) {
            database.update("DELETE FROM " + table);
        }
        String passwordHash = auth.encodePassword(PASSWORD);
        database.update("INSERT INTO accounts VALUES (?, ?, ?, ?, ?)", CAREGIVER, "caregiver", passwordHash, "Caregiver", "CAREGIVER");
        database.update("INSERT INTO accounts VALUES (?, ?, ?, ?, ?)", ADULT, "adult", passwordHash, "Adult", "OLDER_ADULT");
        database.update("INSERT INTO accounts VALUES (?, ?, ?, ?, ?)", OTHER_ADULT, "other", passwordHash, "Other adult", "OLDER_ADULT");
        database.update("INSERT INTO care_links VALUES (?, ?)", CAREGIVER, ADULT);
    }

    @Test
    void loginAttemptsAreLimitedForExistingAndUnknownAccounts() {
        for (String username : new String[]{"adult", "unknown"}) {
            for (int attempt = 0; attempt < 5; attempt++) {
                assertThat(call(HttpMethod.POST, "/auth/sessions", null,
                    Map.of("username", username, "password", "wrong-password")).getStatusCode())
                    .isEqualTo(HttpStatus.UNAUTHORIZED);
            }
            assertThat(call(HttpMethod.POST, "/auth/sessions", null,
                Map.of("username", username, "password", PASSWORD)).getStatusCode())
                .isEqualTo(HttpStatus.TOO_MANY_REQUESTS);
        }
        database.update("UPDATE login_attempts SET expires_at = ?", Timestamp.from(Instant.now().minusSeconds(1)));
        assertThat(call(HttpMethod.POST, "/auth/sessions", null,
            Map.of("username", "adult", "password", PASSWORD)).getStatusCode()).isEqualTo(HttpStatus.OK);
    }

    @Test
    void successfulLoginClearsPreviousFailuresAndDoesNotBlockAnotherAccount() {
        for (int attempt = 0; attempt < 4; attempt++) {
            call(HttpMethod.POST, "/auth/sessions", null, Map.of("username", "adult", "password", "wrong"));
        }
        assertThat(login("caregiver")).isNotBlank();
        assertThat(login("adult")).isNotBlank();
        assertThat(database.queryForObject("SELECT COUNT(*) FROM login_attempts", Integer.class)).isZero();
    }

    @Test
    void inactiveSessionsCannotBeRevivedByUsingTheirToken() {
        String token = login("adult");
        database.update("UPDATE auth_sessions SET last_seen_at = ?", Timestamp.from(Instant.now().minusSeconds(1801)));
        assertThat(call(HttpMethod.GET, "/me", token, null).getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
        assertThat(call(HttpMethod.GET, "/me", token, null).getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
    }

    @Test
    void privateEndpointsRejectAnonymousRequests() {
        assertThat(call(HttpMethod.GET, "/people", null, null).getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
    }

    @Test
    void olderAdultCannotConfigureMedicationsEvenWithDirectApiCall() {
        String token = login("adult");
        var response = call(HttpMethod.POST, "/people/" + ADULT + "/medications", token,
            Map.of("name", "Demo", "instructions", "Fictitious"));
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.FORBIDDEN);
        assertThat(database.queryForObject("SELECT COUNT(*) FROM medications", Integer.class)).isZero();
    }

    @Test
    void caregiverCannotReadOrWriteUnlinkedPerson() {
        String token = login("caregiver");
        assertThat(call(HttpMethod.GET, "/people/" + OTHER_ADULT + "/today", token, null).getStatusCode()).isEqualTo(HttpStatus.FORBIDDEN);
        assertThat(call(HttpMethod.POST, "/people/" + OTHER_ADULT + "/medications", token,
            Map.of("name", "Demo", "instructions", "Fictitious")).getStatusCode()).isEqualTo(HttpStatus.FORBIDDEN);
    }

    @Test
    void caregiverCreatesMedicationAndDailyScheduleVisibleToAdult() {
        String caregiverToken = login("caregiver");
        var medication = call(HttpMethod.POST, "/people/" + ADULT + "/medications", caregiverToken,
            Map.of("name", "Fictitious example", "instructions", "No real treatment"));
        assertThat(medication.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        String medicationId = medication.getBody().get("id").asText();
        String date = LocalDate.now(ZoneId.of("America/Lima")).toString();
        var schedule = call(HttpMethod.POST, "/people/" + ADULT + "/schedules", caregiverToken,
            Map.of("medicationId", medicationId, "localTime", "10:30", "startDate", date));
        assertThat(schedule.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        var plan = call(HttpMethod.GET, "/people/" + ADULT + "/today", login("adult"), null);
        assertThat(plan.getBody().get("doses")).hasSize(1);
        assertThat(plan.getBody().get("doses").get(0).get("status").asText()).isEqualTo("SCHEDULED");
        assertThat(database.queryForObject("SELECT COUNT(*) FROM audit_events", Integer.class)).isEqualTo(2);
    }

    @Test
    void scheduleCannotReferenceAnotherPersonsMedication() {
        UUID medicationId = UUID.randomUUID();
        database.update("INSERT INTO medications(id, person_id, name, instructions) VALUES (?, ?, ?, ?)",
            medicationId, OTHER_ADULT, "Other example", "Fictitious");
        var response = call(HttpMethod.POST, "/people/" + ADULT + "/schedules", login("caregiver"),
            Map.of("medicationId", medicationId.toString(), "localTime", "09:00", "startDate", "2026-10-17"));
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
    }

    @Test
    void invalidDatesAndBlankNamesAreRejected() {
        String token = login("caregiver");
        assertThat(call(HttpMethod.POST, "/people/" + ADULT + "/medications", token,
            Map.of("name", "  ", "instructions", "Fictitious")).getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        var response = call(HttpMethod.POST, "/people/" + ADULT + "/schedules", token,
            Map.of("medicationId", UUID.randomUUID().toString(), "localTime", "09:00", "startDate", "2026-10-18", "endDate", "2026-10-17"));
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
    }

    @Test
    void logoutAndExpiryRevokeAccess() {
        String token = login("adult");
        assertThat(call(HttpMethod.DELETE, "/auth/sessions/current", token, null).getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
        assertThat(call(HttpMethod.GET, "/me", token, null).getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
        String expiringToken = login("adult");
        database.update("UPDATE auth_sessions SET expires_at = ?", Timestamp.from(Instant.now().minusSeconds(1)));
        assertThat(call(HttpMethod.GET, "/me", expiringToken, null).getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
    }

    @Test
    void medicationEditsPreserveOwnershipAndAreAudited() {
        String caregiver = login("caregiver");
        UUID medicationId = UUID.randomUUID();
        database.update("INSERT INTO medications(id, person_id, name, instructions) VALUES (?, ?, ?, ?)",
            medicationId, ADULT, "Before", "Fictitious");
        var edited = call(HttpMethod.PUT, "/people/" + ADULT + "/medications/" + medicationId, caregiver,
            Map.of("name", "Updated example", "instructions", "Updated fictitious instructions"));
        assertThat(edited.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(edited.getBody().get("instructions").asText()).isEqualTo("Updated fictitious instructions");
        assertThat(call(HttpMethod.PUT, "/people/" + ADULT + "/medications/" + medicationId, login("adult"),
            Map.of("name", "Not allowed", "instructions", "Not allowed")).getStatusCode()).isEqualTo(HttpStatus.FORBIDDEN);
        var history = call(HttpMethod.GET, "/people/" + ADULT + "/history", caregiver, null);
        assertThat(history.getBody().get(0).get("action").asText()).isEqualTo("MEDICATION_UPDATED");
        assertThat(call(HttpMethod.GET, "/people/" + OTHER_ADULT + "/history", caregiver, null).getStatusCode()).isEqualTo(HttpStatus.FORBIDDEN);
    }

    @Test
    void pausedSchedulesDisappearFromTodayAndCanBeResumedWithoutDuplicateEvents() {
        UUID medicationId = UUID.randomUUID();
        UUID scheduleId = UUID.randomUUID();
        database.update("INSERT INTO medications(id, person_id, name, instructions) VALUES (?, ?, ?, ?)",
            medicationId, ADULT, "Example", "Fictitious");
        database.update("INSERT INTO schedules(id, medication_id, local_time, start_date) VALUES (?, ?, ?, ?)",
            scheduleId, medicationId, java.sql.Time.valueOf("09:00:00"), java.sql.Date.valueOf("2020-01-01"));
        String caregiver = login("caregiver");
        String path = "/people/" + ADULT + "/schedules/" + scheduleId;
        assertThat(call(HttpMethod.PATCH, path, login("adult"), Map.of("enabled", false)).getStatusCode()).isEqualTo(HttpStatus.FORBIDDEN);
        assertThat(call(HttpMethod.PATCH, path, caregiver, Map.of("enabled", false)).getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(call(HttpMethod.GET, "/people/" + ADULT + "/today", caregiver, null).getBody().get("doses")).isEmpty();
        call(HttpMethod.PATCH, path, caregiver, Map.of("enabled", false));
        assertThat(database.queryForObject("SELECT COUNT(*) FROM audit_events", Integer.class)).isEqualTo(1);
        assertThat(call(HttpMethod.PATCH, path, caregiver, Map.of("enabled", true)).getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(call(HttpMethod.GET, "/people/" + ADULT + "/today", caregiver, null).getBody().get("doses")).hasSize(1);
        assertThat(call(HttpMethod.PATCH, "/people/" + OTHER_ADULT + "/schedules/" + scheduleId, caregiver,
            Map.of("enabled", false)).getStatusCode()).isEqualTo(HttpStatus.FORBIDDEN);
    }

    @Test
    void adultHelpRequestIsDeduplicatedAndOnlyLinkedCaregiverCanResolveIt() {
        String adult = login("adult");
        String caregiver = login("caregiver");
        String path = "/people/" + ADULT + "/help-requests";
        var first = call(HttpMethod.POST, path, adult, null);
        var second = call(HttpMethod.POST, path, adult, null);
        assertThat(first.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(second.getBody().get("id")).isEqualTo(first.getBody().get("id"));
        String resolvePath = path + "/" + first.getBody().get("id").asText();
        assertThat(call(HttpMethod.PATCH, resolvePath, adult, null).getStatusCode()).isEqualTo(HttpStatus.FORBIDDEN);
        assertThat(call(HttpMethod.POST, path, caregiver, null).getStatusCode()).isEqualTo(HttpStatus.FORBIDDEN);
        assertThat(call(HttpMethod.POST, "/people/" + OTHER_ADULT + "/help-requests", adult, null).getStatusCode()).isEqualTo(HttpStatus.FORBIDDEN);
        assertThat(call(HttpMethod.PATCH, resolvePath, caregiver, null).getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(call(HttpMethod.GET, path, adult, null).getBody().get(0).get("status").asText()).isEqualTo("CLOSED");
        assertThat(database.queryForObject("SELECT COUNT(*) FROM audit_events", Integer.class)).isEqualTo(2);
    }

    private String login(String username) {
        var response = call(HttpMethod.POST, "/auth/sessions", null, Map.of("username", username, "password", PASSWORD));
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        return response.getBody().get("token").asText();
    }

    private ResponseEntity<JsonNode> call(HttpMethod method, String path, String token, Object body) {
        HttpHeaders headers = new HttpHeaders();
        if (token != null) {
            headers.setBearerAuth(token);
        }
        headers.setContentType(MediaType.APPLICATION_JSON);
        return client.exchange("/api/v1" + path, method, new HttpEntity<>(body, headers), JsonNode.class);
    }
}
