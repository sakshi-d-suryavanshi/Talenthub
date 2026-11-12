# TalentHub – Campus Placement System

Implements the **Lab 4 Detailed Design**: eight tables, layered architecture
(routes → services → repositories), `check_eligibility` (reports all failures),
hashed passwords, server-side role checks, validation, DB constraints and
controlled status transitions.

## Run in VS Code
1. Unzip and open the `TalentHub` folder in VS Code (needs Python 3.10+).
2. Terminal → New Terminal, then:
   ```
   python -m venv .venv
   # Windows:  .venv\Scripts\activate        macOS/Linux:  source .venv/bin/activate
   pip install -r requirements.txt
   python seed.py        # optional demo data
   python run.py
   ```
3. Open http://127.0.0.1:5000  (or press **F5** and pick "TalentHub: Run").

## Demo logins (after `python seed.py`)
| Role | Email | Password |
|---|---|---|
| Student | asha@student.edu (eligible) / ravi@student.edu (fails criteria) | Password@123 |
| Company | hr@technova.com / hr@dataworks.com | Password@123 |
| Coordinator | coordinator@talenthub.local | Admin@1234 |

Override with env vars `SECRET_KEY`, `COORDINATOR_EMAIL`, `COORDINATOR_PASSWORD`.

## Tests
`python -m unittest discover -s tests -v` (or F5 → "TalentHub: Tests").

## Structure
```
app/routes/          request/response only (main, student, company, coordinator)
app/services.py      business rules: check_eligibility, status transitions, transactions
app/repositories.py  all SQL
app/schema.sql       8-table schema (SQLite, zero setup)
schema_mysql.sql     same schema for MySQL 8 (Lab 4 target DB)
```

## Design decisions / assumptions (confirm against your approved requirements)
- **Database:** runs on SQLite so it works instantly in VS Code. `schema_mysql.sql` is the MySQL
  version; to switch, port the connection in `app/db.py` (all SQL is isolated in `repositories.py`).
- **Eligibility inputs:** `students.active_backlogs` and `job_listings.min_cgpa / max_backlogs /
  allowed_departments` were added as columns on the existing tables (still eight tables).
  Boundaries are inclusive; department is checked only when the job sets a restriction.
- **Duplicates:** `UNIQUE(student_id, job_id)` enabled; one offer per application.
- **Status flow:** Applied → Shortlisted → Scheduled (via interview) → Selected; Rejected from any open
  stage. Offers (Pending/Accepted/Declined) only for Selected applications. Deadline enforced at apply time.
- **Coordinator:** not one of the eight tables, so it is a configured account that can manage all
  applications and the skills catalogue.
- Skills stay as text on students/jobs (the lab's known 3NF compromise); `skills` is a catalogue table.
- Security: salted password hashes, session login, role check on every protected route, ownership checks,
  password hashes never sent to templates, CSRF tokens on all POST forms.
