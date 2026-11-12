"""SERVICE LAYER - business rules, validation, transactions."""
import re
import sqlite3
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

from . import repositories as repo

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Controlled status transitions for applications
TRANSITIONS = {
    "Applied": {"Shortlisted", "Rejected"},
    "Shortlisted": {"Scheduled", "Rejected"},
    "Scheduled": {"Selected", "Rejected"},
    "Selected": set(),
    "Rejected": set(),
}


class ServiceError(Exception):
    """A user-facing business-rule or validation failure."""


# ------------------------------------------------------------------ eligibility
def check_eligibility(student, job):
    """checkEligibility(student, job) -> (eligible: bool, reasons: list[str]).

    Option B from the design: evaluate ALL applicable criteria and return every
    failed reason. Boundaries are inclusive (CGPA == minimum passes, backlogs ==
    maximum passes). Department is checked only if the job defines a restriction.
    """
    if student is None or job is None:
        return False, ["Student or job record not found"]
    reasons = []

    cgpa = student["cgpa"]
    if cgpa is None or not 0 <= cgpa <= 10:
        reasons.append("Student CGPA is missing or invalid")
    elif job["min_cgpa"] is not None and cgpa < job["min_cgpa"]:
        reasons.append(f"CGPA {cgpa} is below the minimum {job['min_cgpa']}")

    backlogs = student["active_backlogs"]
    if backlogs is None or backlogs < 0:
        reasons.append("Active backlog count is missing or invalid")
    elif job["max_backlogs"] is not None and backlogs > job["max_backlogs"]:
        reasons.append(f"{backlogs} active backlog(s) exceeds the maximum allowed {job['max_backlogs']}")

    allowed = [d.strip().lower() for d in (job["allowed_departments"] or "").split(",") if d.strip()]
    if allowed:
        dept = (student["department"] or "").strip().lower()
        if not dept:
            reasons.append("Student department is missing")
        elif dept not in allowed:
            reasons.append(f"Department '{student['department']}' is not in the allowed list "
                           f"({job['allowed_departments']})")

    return (len(reasons) == 0), reasons


# ------------------------------------------------------------------ helpers
def _clean(v):
    return (v or "").strip()


def _num(value, label, lo=None, hi=None, integer=False, required=True):
    value = _clean(value)
    if value == "":
        if required:
            raise ServiceError(f"{label} is required")
        return None
    try:
        n = int(value) if integer else float(value)
    except ValueError:
        raise ServiceError(f"{label} must be a number")
    if (lo is not None and n < lo) or (hi is not None and n > hi):
        raise ServiceError(f"{label} must be between {lo} and {hi}" if hi is not None
                           else f"{label} must be at least {lo}")
    return n


def _check_creds(email, password):
    if not EMAIL_RE.match(email):
        raise ServiceError("Enter a valid email address")
    if len(password) < 8:
        raise ServiceError("Password must be at least 8 characters")


def _date(value, label, required=True):
    value = _clean(value)
    if not value:
        if required:
            raise ServiceError(f"{label} is required")
        return None
    try:
        date.fromisoformat(value)
    except ValueError:
        raise ServiceError(f"{label} must be a valid date")
    return value


# ------------------------------------------------------------------ accounts
def register_student(db, f):
    name, email, pw = _clean(f.get("name")), _clean(f.get("email")).lower(), f.get("password") or ""
    if not name or not _clean(f.get("department")):
        raise ServiceError("Name and department are required")
    _check_creds(email, pw)
    year = _num(f.get("year"), "Year", 1, 6, integer=True)
    cgpa = _num(f.get("cgpa"), "CGPA", 0, 10)
    backlogs = _num(f.get("active_backlogs") or "0", "Active backlogs", 0, integer=True)
    try:
        with db:
            return repo.create_student(db, name, email, generate_password_hash(pw),
                                       _clean(f.get("department")), year, cgpa, backlogs,
                                       _clean(f.get("skills")))
    except sqlite3.IntegrityError:
        raise ServiceError("That email is already registered")


def register_company(db, f):
    name, email, pw = _clean(f.get("company_name")), _clean(f.get("email")).lower(), f.get("password") or ""
    if not name:
        raise ServiceError("Company name is required")
    _check_creds(email, pw)
    try:
        with db:
            return repo.create_company(db, name, email, generate_password_hash(pw),
                                       _clean(f.get("industry")), _clean(f.get("location")))
    except sqlite3.IntegrityError:
        raise ServiceError("That email is already registered")


def authenticate(db, config, role, email, password):
    """Return the user id (or 'coordinator') if credentials are valid, else None."""
    email = _clean(email).lower()
    if role == "student":
        u = repo.get_student_by_email(db, email)
        return u["student_id"] if u and check_password_hash(u["password_hash"], password) else None
    if role == "company":
        u = repo.get_company_by_email(db, email)
        return u["company_id"] if u and check_password_hash(u["password_hash"], password) else None
    if role == "coordinator":
        ok = email == config["COORDINATOR_EMAIL"].lower() and \
            check_password_hash(config["COORDINATOR_HASH"], password)
        return 0 if ok else None
    return None


def update_profile(db, student_id, f):
    dept = _clean(f.get("department"))
    if not dept:
        raise ServiceError("Department is required")
    with db:
        repo.update_student(db, student_id, dept, _num(f.get("year"), "Year", 1, 6, integer=True),
                            _num(f.get("cgpa"), "CGPA", 0, 10),
                            _num(f.get("active_backlogs") or "0", "Active backlogs", 0, integer=True),
                            _clean(f.get("skills")))


# ------------------------------------------------------------------ jobs
def create_job(db, company_id, f):
    title = _clean(f.get("job_title"))
    if not title:
        raise ServiceError("Job title is required")
    min_cgpa = _num(f.get("min_cgpa") or "0", "Minimum CGPA", 0, 10)
    max_b = _num(f.get("max_backlogs"), "Maximum backlogs", 0, integer=True, required=False)
    salary = _num(f.get("salary"), "Salary", 0, required=False)
    deadline = _date(f.get("deadline"), "Deadline", required=False)
    with db:
        return repo.create_job(db, company_id, title, _clean(f.get("description")),
                               _clean(f.get("eligibility_criteria")), min_cgpa, max_b,
                               _clean(f.get("allowed_departments")), _clean(f.get("required_skills")),
                               salary, deadline)


# ------------------------------------------------------------------ applications
def apply_to_job(db, student_id, job_id):
    student, job = repo.get_student(db, student_id), repo.get_job(db, job_id)
    if not student or not job:
        raise ServiceError("Student or job not found")
    if job["deadline"] and job["deadline"] < date.today().isoformat():
        raise ServiceError("The application deadline for this job has passed")
    ok, reasons = check_eligibility(student, job)
    if not ok:
        raise ServiceError("Not eligible: " + "; ".join(reasons))
    try:
        with db:  # one transaction: application + notification
            app_id = repo.create_application(db, student_id, job_id, date.today().isoformat())
            repo.add_notification(db, student_id,
                                  f"Application submitted for {job['job_title']} at {job['company_name']}.")
        return app_id
    except sqlite3.IntegrityError:
        raise ServiceError("You have already applied for this job")


def can_manage(user, application):
    """Server-side ownership check for company users and the coordinator."""
    if user["role"] == "coordinator":
        return True
    return user["role"] == "company" and application["company_id"] == user["id"]


def change_status(db, application_id, new_status):
    app = repo.get_application(db, application_id)
    if not app:
        raise ServiceError("Application not found")
    if new_status not in TRANSITIONS.get(app["status"], set()):
        raise ServiceError(f"Cannot change status from {app['status']} to {new_status}")
    if new_status == "Scheduled":
        raise ServiceError("Status becomes Scheduled when you schedule an interview")
    with db:
        repo.set_application_status(db, application_id, new_status)
        repo.add_notification(db, app["student_id"],
                              f"Your application for {app['job_title']} is now '{new_status}'.")


def schedule_interview(db, application_id, f):
    app = repo.get_application(db, application_id)
    if not app:
        raise ServiceError("Application not found")
    if app["status"] not in ("Shortlisted", "Scheduled"):
        raise ServiceError("Only shortlisted applications can be scheduled for interview")
    d = _date(f.get("interview_date"), "Interview date")
    t = _clean(f.get("interview_time"))
    if not t:
        raise ServiceError("Interview time is required")
    mode = f.get("interview_mode")
    if mode not in ("Online", "Offline"):
        raise ServiceError("Interview mode must be Online or Offline")
    with db:
        repo.create_interview(db, application_id, d, t, mode)
        if app["status"] == "Shortlisted":
            repo.set_application_status(db, application_id, "Scheduled")
        repo.add_notification(db, app["student_id"],
                              f"Interview for {app['job_title']} scheduled on {d} at {t} ({mode}).")


def make_offer(db, application_id, f):
    app = repo.get_application(db, application_id)
    if not app:
        raise ServiceError("Application not found")
    if app["status"] != "Selected":
        raise ServiceError("An offer can only be made for a Selected application")
    if repo.offer_by_application(db, application_id):
        raise ServiceError("An offer already exists for this application")
    salary = _num(f.get("salary"), "Salary", 0, required=False)
    joining = _date(f.get("joining_date"), "Joining date", required=False)
    try:
        with db:
            repo.create_offer(db, application_id, date.today().isoformat(), salary, joining)
            repo.add_notification(db, app["student_id"],
                                  f"You have received an offer for {app['job_title']} from {app['company_name']}.")
    except sqlite3.IntegrityError:
        raise ServiceError("An offer already exists for this application")


def respond_offer(db, student_id, offer_id, decision):
    offer = repo.get_offer(db, offer_id)
    if not offer or offer["student_id"] != student_id:
        raise ServiceError("Offer not found")
    if decision not in ("Accepted", "Declined"):
        raise ServiceError("Invalid decision")
    if offer["status"] != "Pending":
        raise ServiceError("This offer has already been answered")
    with db:
        repo.set_offer_status(db, offer_id, decision)
        repo.add_notification(db, student_id, f"You {decision.lower()} the offer for {offer['job_title']}.")


def add_skill(db, name, skill_type):
    name = _clean(name)
    if not name:
        raise ServiceError("Skill name is required")
    try:
        with db:
            repo.add_skill(db, name, _clean(skill_type))
    except sqlite3.IntegrityError:
        raise ServiceError("That skill already exists")
