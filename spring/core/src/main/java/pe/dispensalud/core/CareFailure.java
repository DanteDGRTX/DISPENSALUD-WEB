package pe.dispensalud.core;

public final class CareFailure extends RuntimeException {
    public enum Kind { CONFLICT, NOT_FOUND, FORBIDDEN, UNAVAILABLE, LIMIT }
    private final Kind kind;
    public CareFailure(Kind kind, String message) { super(message); this.kind = kind; }
    public Kind kind() { return kind; }
}
