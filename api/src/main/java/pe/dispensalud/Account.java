package pe.dispensalud;

import java.util.UUID;

public record Account(UUID id, String username, String displayName, String role) {
    public boolean isCaregiver() {
        return "CAREGIVER".equals(role);
    }
}
