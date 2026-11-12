import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import create_app
from app import services as svc


def S(cgpa=8, backlogs=0, dept="CSE"):
    return {"cgpa": cgpa, "active_backlogs": backlogs, "department": dept}


def J(min_cgpa=7, max_b=1, depts=""):
    return {"min_cgpa": min_cgpa, "max_backlogs": max_b, "allowed_departments": depts}


class EligibilityTests(unittest.TestCase):
    def test_eligible(self):
        self.assertEqual(svc.check_eligibility(S(), J()), (True, []))

    def test_cgpa_boundary_inclusive(self):
        self.assertTrue(svc.check_eligibility(S(cgpa=7), J(min_cgpa=7))[0])
        self.assertFalse(svc.check_eligibility(S(cgpa=6.99), J(min_cgpa=7))[0])

    def test_backlog_boundary_inclusive(self):
        self.assertTrue(svc.check_eligibility(S(backlogs=1), J(max_b=1))[0])
        self.assertFalse(svc.check_eligibility(S(backlogs=2), J(max_b=1))[0])

    def test_no_backlog_limit_and_no_dept_restriction(self):
        self.assertTrue(svc.check_eligibility(S(backlogs=9, dept="MECH"), J(max_b=None))[0])

    def test_all_failures_reported(self):
        ok, reasons = svc.check_eligibility(S(cgpa=5, backlogs=3, dept="ECE"), J(7, 1, "CSE, IT"))
        self.assertFalse(ok)
        self.assertEqual(len(reasons), 3)

    def test_missing_records(self):
        self.assertFalse(svc.check_eligibility(None, J())[0])


class FlowTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.app = create_app({"DATABASE": self.path, "TESTING": True})
        self.c = self.app.test_client()

    def tearDown(self):
        os.remove(self.path)

    def post(self, url, **data):
        return self.c.post(url, data=data, follow_redirects=True)

    def login(self, role, email, pw="Password@123"):
        self.c.post("/logout")
        return self.post("/login", role=role, email=email, password=pw)

    def test_full_flow(self):
        self.post("/register/company", company_name="Acme", email="hr@acme.com", password="Password@123")
        self.post("/register/student", name="A", email="a@x.com", password="Password@123", department="CSE",
                  year="4", cgpa="8", active_backlogs="0", skills="Python")
        self.post("/register/student", name="B", email="b@x.com", password="Password@123", department="ECE",
                  year="4", cgpa="5", active_backlogs="3", skills="")
        self.login("company", "hr@acme.com")
        self.post("/company/jobs/new", job_title="Dev", min_cgpa="7", max_backlogs="0",
                  allowed_departments="CSE", salary="500000")
        # ineligible student is blocked server-side
        self.login("student", "b@x.com")
        r = self.post("/student/apply/1")
        self.assertIn(b"Not eligible", r.data)
        # eligible student applies; duplicate blocked
        self.login("student", "a@x.com")
        self.assertIn(b"Application submitted", self.post("/student/apply/1").data)
        self.assertIn(b"already applied", self.post("/student/apply/1").data)
        # role isolation: student cannot reach company pages
        self.assertEqual(self.c.get("/company/dashboard").status_code, 403)
        # company drives the pipeline
        self.login("company", "hr@acme.com")
        self.assertIn(b"Cannot change status", self.post("/manage/applications/1/status", status="Selected").data)
        self.post("/manage/applications/1/status", status="Shortlisted")
        self.post("/manage/applications/1/interview", interview_date="2030-01-01",
                  interview_time="10:00", interview_mode="Online")
        self.post("/manage/applications/1/status", status="Selected")
        self.assertIn(b"Offer created", self.post("/manage/applications/1/offer", salary="500000").data)
        self.assertIn(b"already exists", self.post("/manage/applications/1/offer", salary="1").data)
        # another company cannot manage it
        self.post("/register/company", company_name="Other", email="hr@other.com", password="Password@123")
        self.login("company", "hr@other.com")
        self.assertEqual(self.c.get("/manage/applications/1").status_code, 403)
        # student accepts offer and sees notifications
        self.login("student", "a@x.com")
        self.post("/student/offers/1/respond", decision="Accepted")
        page = self.c.get("/student/dashboard").data
        self.assertIn(b"Accepted", page)
        self.assertNotIn(b"pbkdf2", page)
        self.assertNotIn(b"scrypt", page)

    def test_coordinator_and_bad_login(self):
        self.assertIn(b"Invalid email", self.login("coordinator", "coordinator@talenthub.local", "wrong").data)
        self.login("coordinator", "coordinator@talenthub.local", "Admin@1234")
        self.assertEqual(self.c.get("/coordinator/dashboard").status_code, 200)
        self.assertIn(b"Skill added", self.post("/coordinator/skills", skill_name="Go", skill_type="Prog").data)


if __name__ == "__main__":
    unittest.main()
