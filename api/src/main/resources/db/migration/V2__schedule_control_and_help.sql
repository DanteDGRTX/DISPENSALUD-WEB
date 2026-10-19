ALTER TABLE schedules ADD COLUMN enabled BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE audit_events ADD COLUMN person_id UUID REFERENCES accounts(id);
UPDATE audit_events SET person_id = (SELECT person_id FROM medications WHERE medications.id = audit_events.object_id)
WHERE action = 'MEDICATION_CREATED';
UPDATE audit_events SET person_id = (SELECT m.person_id FROM medications m JOIN schedules s ON s.medication_id = m.id WHERE s.id = audit_events.object_id)
WHERE action = 'SCHEDULE_CREATED';
ALTER TABLE audit_events ALTER COLUMN person_id SET NOT NULL;
CREATE INDEX audit_events_person_idx ON audit_events(person_id, occurred_at);
CREATE TABLE help_requests (
    id UUID PRIMARY KEY,
    person_id UUID NOT NULL REFERENCES accounts(id),
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);
CREATE INDEX help_requests_person_idx ON help_requests(person_id, status);
