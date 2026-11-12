"""Load demo data:  python seed.py   (safe to run once on a fresh database)."""
from werkzeug.security import generate_password_hash
from app import create_app
from app.db import get_db
from app import repositories as repo

app = create_app()
with app.app_context():
    db = get_db()
    if repo.get_student_by_email(db, "asha@student.edu"):
        print("Demo data already present.")
        raise SystemExit
    with db:
        for n, t in [("Python", "Programming"), ("Java", "Programming"), ("SQL", "Database"),
                     ("Machine Learning", "AI"), ("Communication", "Soft skill")]:
            repo.add_skill(db, n, t)
        pw = generate_password_hash("Password@123")
        repo.create_student(db, "Asha Rao", "asha@student.edu", pw, "CSE", 4, 8.4, 0, "Python, SQL")
        repo.create_student(db, "Ravi Kumar", "ravi@student.edu", pw, "ECE", 4, 6.2, 2, "Java")
        c1 = repo.create_company(db, "TechNova", "hr@technova.com", pw, "Software", "Bengaluru")
        c2 = repo.create_company(db, "DataWorks", "hr@dataworks.com", pw, "Analytics", "Pune")
        repo.create_job(db, c1, "Software Engineer", "Build backend services.", "", 7.0, 0, "CSE, IT",
                        "Python, SQL", 800000, "2030-12-31")
        repo.create_job(db, c2, "Data Analyst", "Analyse placement data.", "", 6.0, 1, "", "SQL", 600000, "2030-12-31")
        repo.create_job(db, c1, "Support Engineer", "Customer support.", "", 5.0, None, "", "Communication", 400000, "2030-12-31")
print("Seeded. Logins (password for all demo users: Password@123):")
print("  student:     asha@student.edu (eligible for most)  /  ravi@student.edu (fails some criteria)")
print("  company:     hr@technova.com  /  hr@dataworks.com")
print("  coordinator: coordinator@talenthub.local  /  Admin@1234")
