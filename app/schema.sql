PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS students (
    student_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    department      TEXT NOT NULL,
    year            INTEGER NOT NULL CHECK (year BETWEEN 1 AND 6),
    cgpa            REAL NOT NULL CHECK (cgpa BETWEEN 0 AND 10),
    active_backlogs INTEGER NOT NULL DEFAULT 0 CHECK (active_backlogs >= 0),
    skills          TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS companies (
    company_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name  TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    industry      TEXT,
    location      TEXT
);

CREATE TABLE IF NOT EXISTS job_listings (
    job_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id           INTEGER NOT NULL REFERENCES companies(company_id),
    job_title            TEXT NOT NULL,
    description          TEXT,
    eligibility_criteria TEXT,
    min_cgpa             REAL NOT NULL DEFAULT 0 CHECK (min_cgpa BETWEEN 0 AND 10),
    max_backlogs         INTEGER CHECK (max_backlogs IS NULL OR max_backlogs >= 0),
    allowed_departments  TEXT DEFAULT '',
    required_skills      TEXT DEFAULT '',
    salary               REAL CHECK (salary IS NULL OR salary >= 0),
    deadline             TEXT
);

CREATE TABLE IF NOT EXISTS applications (
    application_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id       INTEGER NOT NULL REFERENCES students(student_id),
    job_id           INTEGER NOT NULL REFERENCES job_listings(job_id),
    application_date TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'Applied'
        CHECK (status IN ('Applied','Shortlisted','Rejected','Scheduled','Selected')),
    UNIQUE (student_id, job_id)
);

CREATE TABLE IF NOT EXISTS interview_slots (
    interview_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(application_id),
    interview_date TEXT NOT NULL,
    interview_time TEXT NOT NULL,
    interview_mode TEXT NOT NULL CHECK (interview_mode IN ('Online','Offline')),
    status         TEXT NOT NULL DEFAULT 'Scheduled'
        CHECK (status IN ('Scheduled','Completed','Cancelled'))
);

CREATE TABLE IF NOT EXISTS offers (
    offer_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL UNIQUE REFERENCES applications(application_id),
    offer_date     TEXT NOT NULL,
    salary         REAL CHECK (salary IS NULL OR salary >= 0),
    joining_date   TEXT,
    status         TEXT NOT NULL DEFAULT 'Pending'
        CHECK (status IN ('Pending','Accepted','Declined'))
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL UNIQUE,
    skill_type TEXT
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id        INTEGER NOT NULL REFERENCES students(student_id),
    message           TEXT NOT NULL,
    notification_date TEXT NOT NULL,
    is_read           INTEGER NOT NULL DEFAULT 0 CHECK (is_read IN (0,1))
);
