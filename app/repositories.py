"""REPOSITORY LAYER - all SQL lives here. No business rules, no commits
(services control transactions with `with db:`)."""
from datetime import datetime


# ---- students ----
def create_student(db, name, email, password_hash, department, year, cgpa, backlogs, skills):
    cur = db.execute(
        "INSERT INTO students (name,email,password_hash,department,year,cgpa,active_backlogs,skills)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (name, email, password_hash, department, year, cgpa, backlogs, skills))
    return cur.lastrowid


def get_student(db, student_id):
    return db.execute("SELECT * FROM students WHERE student_id=?", (student_id,)).fetchone()


def get_student_by_email(db, email):
    return db.execute("SELECT * FROM students WHERE email=?", (email,)).fetchone()


def update_student(db, student_id, department, year, cgpa, backlogs, skills):
    db.execute("UPDATE students SET department=?, year=?, cgpa=?, active_backlogs=?, skills=?"
               " WHERE student_id=?", (department, year, cgpa, backlogs, skills, student_id))


# ---- companies ----
def create_company(db, name, email, password_hash, industry, location):
    cur = db.execute("INSERT INTO companies (company_name,email,password_hash,industry,location)"
                     " VALUES (?,?,?,?,?)", (name, email, password_hash, industry, location))
    return cur.lastrowid


def get_company(db, company_id):
    return db.execute("SELECT * FROM companies WHERE company_id=?", (company_id,)).fetchone()


def get_company_by_email(db, email):
    return db.execute("SELECT * FROM companies WHERE email=?", (email,)).fetchone()


# ---- jobs ----
JOB_SELECT = ("SELECT j.*, c.company_name, c.location FROM job_listings j "
              "JOIN companies c ON c.company_id=j.company_id ")


def create_job(db, company_id, title, description, criteria, min_cgpa, max_backlogs,
               departments, required_skills, salary, deadline):
    cur = db.execute(
        "INSERT INTO job_listings (company_id,job_title,description,eligibility_criteria,min_cgpa,"
        "max_backlogs,allowed_departments,required_skills,salary,deadline) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (company_id, title, description, criteria, min_cgpa, max_backlogs, departments,
         required_skills, salary, deadline))
    return cur.lastrowid


def get_job(db, job_id):
    return db.execute(JOB_SELECT + "WHERE j.job_id=?", (job_id,)).fetchone()


def list_jobs(db, search=""):
    like = f"%{search}%"
    return db.execute(JOB_SELECT + "WHERE j.job_title LIKE ? OR c.company_name LIKE ? "
                      "OR j.required_skills LIKE ? ORDER BY j.job_id DESC", (like, like, like)).fetchall()


def jobs_by_company(db, company_id):
    return db.execute(
        "SELECT j.*, (SELECT COUNT(*) FROM applications a WHERE a.job_id=j.job_id) AS applicants "
        "FROM job_listings j WHERE j.company_id=? ORDER BY j.job_id DESC", (company_id,)).fetchall()


# ---- applications ----
APP_SELECT = ("SELECT a.*, s.name AS student_name, s.department, s.cgpa, s.active_backlogs, s.skills, "
              "j.job_title, j.company_id, c.company_name FROM applications a "
              "JOIN students s ON s.student_id=a.student_id "
              "JOIN job_listings j ON j.job_id=a.job_id "
              "JOIN companies c ON c.company_id=j.company_id ")


def create_application(db, student_id, job_id, date):
    cur = db.execute("INSERT INTO applications (student_id,job_id,application_date) VALUES (?,?,?)",
                     (student_id, job_id, date))
    return cur.lastrowid


def get_application(db, application_id):
    return db.execute(APP_SELECT + "WHERE a.application_id=?", (application_id,)).fetchone()


def applications_by_student(db, student_id):
    return db.execute(APP_SELECT + "WHERE a.student_id=? ORDER BY a.application_id DESC",
                      (student_id,)).fetchall()


def applications_by_job(db, job_id):
    return db.execute(APP_SELECT + "WHERE a.job_id=? ORDER BY a.application_id DESC", (job_id,)).fetchall()


def all_applications(db):
    return db.execute(APP_SELECT + "ORDER BY a.application_id DESC").fetchall()


def set_application_status(db, application_id, status):
    db.execute("UPDATE applications SET status=? WHERE application_id=?", (status, application_id))


# ---- interviews ----
def create_interview(db, application_id, date, time, mode):
    db.execute("INSERT INTO interview_slots (application_id,interview_date,interview_time,interview_mode)"
               " VALUES (?,?,?,?)", (application_id, date, time, mode))


def interviews_by_application(db, application_id):
    return db.execute("SELECT * FROM interview_slots WHERE application_id=? ORDER BY interview_date",
                      (application_id,)).fetchall()


# ---- offers ----
def create_offer(db, application_id, date, salary, joining_date):
    cur = db.execute("INSERT INTO offers (application_id,offer_date,salary,joining_date) VALUES (?,?,?,?)",
                     (application_id, date, salary, joining_date))
    return cur.lastrowid


def get_offer(db, offer_id):
    return db.execute(
        "SELECT o.*, a.student_id, j.job_title, c.company_name FROM offers o "
        "JOIN applications a ON a.application_id=o.application_id "
        "JOIN job_listings j ON j.job_id=a.job_id JOIN companies c ON c.company_id=j.company_id "
        "WHERE o.offer_id=?", (offer_id,)).fetchone()


def offer_by_application(db, application_id):
    return db.execute("SELECT * FROM offers WHERE application_id=?", (application_id,)).fetchone()


def offers_by_student(db, student_id):
    return db.execute(
        "SELECT o.*, j.job_title, c.company_name FROM offers o "
        "JOIN applications a ON a.application_id=o.application_id "
        "JOIN job_listings j ON j.job_id=a.job_id JOIN companies c ON c.company_id=j.company_id "
        "WHERE a.student_id=? ORDER BY o.offer_id DESC", (student_id,)).fetchall()


def set_offer_status(db, offer_id, status):
    db.execute("UPDATE offers SET status=? WHERE offer_id=?", (status, offer_id))


# ---- skills ----
def list_skills(db):
    return db.execute("SELECT * FROM skills ORDER BY skill_name").fetchall()


def add_skill(db, name, skill_type):
    db.execute("INSERT INTO skills (skill_name,skill_type) VALUES (?,?)", (name, skill_type))


# ---- notifications ----
def add_notification(db, student_id, message):
    db.execute("INSERT INTO notifications (student_id,message,notification_date) VALUES (?,?,?)",
               (student_id, message, datetime.now().strftime("%Y-%m-%d %H:%M")))


def notifications_by_student(db, student_id):
    return db.execute("SELECT * FROM notifications WHERE student_id=? ORDER BY notification_id DESC",
                      (student_id,)).fetchall()


def mark_notifications_read(db, student_id):
    db.execute("UPDATE notifications SET is_read=1 WHERE student_id=?", (student_id,))
