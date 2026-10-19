package pe.dispensalud;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1")
public class ApiController {
    private final AuthService auth;
    private final CareService care;

    public ApiController(AuthService auth, CareService care) {
        this.auth = auth;
        this.care = care;
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "ok", "service", "dispensalud-api");
    }

    @PostMapping("/auth/sessions")
    public AuthService.Session login(@Valid @RequestBody LoginInput input) {
        return auth.login(input.username(), input.password());
    }

    @DeleteMapping("/auth/sessions/current")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void logout(@RequestHeader("Authorization") String authorization) {
        auth.logout(authorization.substring(7));
    }

    @GetMapping("/me")
    public Account me(@AuthenticationPrincipal Account account) {
        return account;
    }

    @GetMapping("/people")
    public List<CareService.Person> people(@AuthenticationPrincipal Account actor) {
        return care.people(actor);
    }

    @GetMapping("/people/{personId}/medications")
    public List<CareService.Medication> medications(@AuthenticationPrincipal Account actor, @PathVariable UUID personId) {
        return care.medications(actor, personId);
    }

    @PostMapping("/people/{personId}/medications")
    @ResponseStatus(HttpStatus.CREATED)
    public CareService.Medication addMedication(@AuthenticationPrincipal Account actor,
            @PathVariable UUID personId, @Valid @RequestBody MedicationInput input) {
        return care.addMedication(actor, personId, input.name(), input.instructions());
    }

    @PostMapping("/people/{personId}/schedules")
    @ResponseStatus(HttpStatus.CREATED)
    public Map<String, UUID> addSchedule(@AuthenticationPrincipal Account actor,
            @PathVariable UUID personId, @Valid @RequestBody ScheduleInput input) {
        return care.addSchedule(actor, personId, input.medicationId(), input.localTime(), input.startDate(), input.endDate());
    }

    @PutMapping("/people/{personId}/medications/{medicationId}")
    public CareService.Medication updateMedication(@AuthenticationPrincipal Account actor, @PathVariable UUID personId,
            @PathVariable UUID medicationId, @Valid @RequestBody MedicationInput input) {
        return care.updateMedication(actor, personId, medicationId, input.name(), input.instructions());
    }

    @GetMapping("/people/{personId}/schedules")
    public List<CareService.Schedule> schedules(@AuthenticationPrincipal Account actor, @PathVariable UUID personId) {
        return care.schedules(actor, personId);
    }

    @PatchMapping("/people/{personId}/schedules/{scheduleId}")
    public Map<String, Boolean> setScheduleEnabled(@AuthenticationPrincipal Account actor, @PathVariable UUID personId,
            @PathVariable UUID scheduleId, @Valid @RequestBody ScheduleState input) {
        return care.setScheduleEnabled(actor, personId, scheduleId, input.enabled());
    }

    @GetMapping("/people/{personId}/history")
    public List<CareService.HistoryEvent> history(@AuthenticationPrincipal Account actor, @PathVariable UUID personId) {
        return care.history(actor, personId);
    }

    @GetMapping("/people/{personId}/help-requests")
    public List<CareService.HelpRequest> helpRequests(@AuthenticationPrincipal Account actor, @PathVariable UUID personId) {
        return care.helpRequests(actor, personId);
    }

    @PostMapping("/people/{personId}/help-requests")
    public Map<String, UUID> requestHelp(@AuthenticationPrincipal Account actor, @PathVariable UUID personId) {
        return care.requestHelp(actor, personId);
    }

    @PatchMapping("/people/{personId}/help-requests/{requestId}")
    public Map<String, String> resolveHelp(@AuthenticationPrincipal Account actor, @PathVariable UUID personId,
            @PathVariable UUID requestId) {
        return care.resolveHelp(actor, personId, requestId);
    }

    @GetMapping("/people/{personId}/today")
    public CareService.DayPlan today(@AuthenticationPrincipal Account actor, @PathVariable UUID personId) {
        return care.today(actor, personId);
    }

    public record LoginInput(@NotBlank @Size(max = 100) String username,
        @NotBlank @Size(max = 60) String password) { }
    public record MedicationInput(@NotBlank @Size(max = 120) String name,
        @NotBlank @Size(max = 500) String instructions) { }
    public record ScheduleInput(@NotNull UUID medicationId, @NotNull LocalTime localTime,
        @NotNull LocalDate startDate, LocalDate endDate) { }
    public record ScheduleState(@NotNull Boolean enabled) { }
}
