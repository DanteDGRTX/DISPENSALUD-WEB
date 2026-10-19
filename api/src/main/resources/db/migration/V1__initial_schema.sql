CREATE TABLE accounts (
    id UUID PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(100) NOT NULL,
    display_name VARCHAR(120) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('CAREGIVER', 'OLDER_ADULT'))
);
CREATE TABLE care_links (
    caregiver_id UUID NOT NULL REFERENCES accounts(id),
    person_id UUID NOT NULL REFERENCES accounts(id),
    PRIMARY KEY (caregiver_id, person_id)
);
CREATE TABLE auth_sessions (
    token_hash VARCHAR(64) PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES accounts(id),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE TABLE medications (
    id UUID PRIMARY KEY,
    person_id UUID NOT NULL REFERENCES accounts(id),
    name VARCHAR(120) NOT NULL,
    instructions VARCHAR(500) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE schedules (
    id UUID PRIMARY KEY,
    medication_id UUID NOT NULL REFERENCES medications(id),
    local_time TIME NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    timezone VARCHAR(80) NOT NULL DEFAULT 'America/Lima',
    UNIQUE (medication_id, local_time, start_date),
    CHECK (end_date IS NULL OR end_date >= start_date)
);
CREATE TABLE audit_events (
    id UUID PRIMARY KEY,
    actor_id UUID NOT NULL REFERENCES accounts(id),
    action VARCHAR(80) NOT NULL,
    object_id UUID NOT NULL,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX medications_person_idx ON medications(person_id);
CREATE INDEX auth_sessions_expiry_idx ON auth_sessions(expires_at);
