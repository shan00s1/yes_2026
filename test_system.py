import unittest
import json
import os
import time
from app import app
from database import init_db, get_db

class TestYES2026EventSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()
        init_db()
        with cls.client.session_transaction() as sess:
            sess["admin_logged_in"] = True
        cls.client.post("/api/admin/clear-all")

    def test_01_participant_registration(self):
        payload = {
            "category": "participant",
            "full_name": "Rohan Deshmukh",
            "email": "rohan.deshmukh@vtu.ac.in",
            "phone": "+91-98765-43210",
            "organization": "VTU Centre for Post Graduate Studies",
            "designation": "Student Innovator",
            "track_or_industry": "Deep-Tech & IoT",
            "custom_fields": {
                "tshirt_size": "L",
                "portfolio_url": "https://github.com/rohandev",
                "interests": "Autonomous AI & Smart Sensors"
            }
        }
        res = self.client.post("/api/register", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["registration_id"].startswith("YES26-PAR-"))
        self.assertIn("qr_code_base64", data)
        self.assertEqual(data["attendee"]["full_name"], "Rohan Deshmukh")
        self.assertEqual(data["attendee"]["category"], "participant")

    def test_02_delegate_registration(self):
        payload = {
            "category": "delegate",
            "full_name": "Pooja Patil",
            "email": "pooja.patil@ktech.org",
            "phone": "+91-98765-11223",
            "organization": "K-tech Innovation Hub",
            "designation": "Director Regional Partnerships",
            "track_or_industry": "Incubation & Policy",
            "custom_fields": {
                "b2b_networking": "Yes - High Priority",
                "tax_id": "GSTIN-29AAACV1234F1Z5"
            }
        }
        res = self.client.post("/api/register", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["registration_id"].startswith("YES26-DEL-"))
        self.assertEqual(data["attendee"]["category"], "delegate")

    def test_03_faculty_registration(self):
        payload = {
            "category": "faculty",
            "full_name": "Prof. S. Vidyashankar",
            "email": "vc@vtu.ac.in",
            "phone": "+91-831-2498100",
            "organization": "Visvesvaraya Technological University (VTU)",
            "designation": "Vice Chancellor & Senior Academician",
            "track_or_industry": "Higher Technical Education & Innovation",
            "custom_fields": {
                "title": "Prof.",
                "academic_role": "Professor & Vice Chancellor",
                "department": "Mechanical & Advanced Manufacturing",
                "college_code": "VTU-HQ-01",
                "engagement_role": "Startup Mentor / Pitch Evaluator",
                "specialization": "Smart Manufacturing & Autonomous Systems"
            }
        }
        res = self.client.post("/api/register", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["registration_id"].startswith("YES26-FAC-"))
        self.assertEqual(data["attendee"]["category"], "faculty")
        
        # Test viewing the rendered email
        email_res = self.client.get(f"/api/emails/latest/{data['registration_id']}")
        self.assertEqual(email_res.status_code, 200)
        self.assertIn(b"FACULTY", email_res.data)
        self.assertIn(b"Prof. S. Vidyashankar", email_res.data)

        # Verify legacy 'vip' category alias gracefully produces FAC pass
        legacy_payload = {
            "category": "vip",
            "full_name": "Dr. Legacy Dignitary",
            "email": "legacy.vip@vtu.ac.in",
            "phone": "+91-99999-00000",
            "organization": "VTU Academic Council"
        }
        legacy_res = self.client.post("/api/register", json=legacy_payload)
        self.assertEqual(legacy_res.status_code, 200)
        legacy_data = legacy_res.get_json()
        self.assertTrue(legacy_data["registration_id"].startswith("YES26-FAC-"))
        self.assertEqual(legacy_data["attendee"]["category"], "faculty")

    def test_04_checkin_and_duplicate_prevention(self):
        # 1. Register attendee
        payload = {
            "category": "participant",
            "full_name": "Checkin Tester",
            "email": "checkin.tester@test.com",
            "phone": "+91-99999-11111",
            "organization": "Test Academy Belagavi"
        }
        reg_res = self.client.post("/api/register", json=payload)
        reg_data = reg_res.get_json()
        reg_id = reg_data["registration_id"]

        # 2. First check-in scan -> MUST SUCCEED
        scan_res1 = self.client.post("/api/checkin/scan", json={"code": reg_id, "station": "Station Alpha"})
        self.assertEqual(scan_res1.status_code, 200)
        data1 = scan_res1.get_json()
        self.assertTrue(data1["success"])
        self.assertEqual(data1["attendee"]["status"], "CHECKED_IN")
        self.assertIsNotNone(data1["attendee"]["check_in_time"])
        initial_checkin_time = data1["attendee"]["check_in_time"]

        # 3. Second check-in scan -> MUST DETECT DUPLICATE & PREVENT RE-ENTRY
        scan_res2 = self.client.post("/api/checkin/scan", json={"code": reg_id, "station": "Station Beta"})
        self.assertEqual(scan_res2.status_code, 200)
        data2 = scan_res2.get_json()
        self.assertFalse(data2["success"])
        self.assertEqual(data2["error_type"], "DUPLICATE")
        self.assertIn("already checked in", data2["message"])
        self.assertEqual(data2["check_in_time"], initial_checkin_time)

    def test_05_admin_apis_and_csv_export(self):
        # Stats
        stats_res = self.client.get("/api/admin/stats")
        self.assertEqual(stats_res.status_code, 200)
        stats = stats_res.get_json()["stats"]
        self.assertGreaterEqual(stats["total"], 4)
        self.assertGreaterEqual(stats["checked_in"], 1)

        # CSV Export
        csv_res = self.client.get("/api/admin/export/csv")
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res.mimetype, "text/csv")
        self.assertIn(b"Registration ID,Category,Full Name", csv_res.data)

    def test_06_dynamic_event_apis(self):
        # Verify dynamic event info
        info_res = self.client.get("/api/event/info")
        self.assertEqual(info_res.status_code, 200)
        info = info_res.get_json()["event"]
        self.assertEqual(info["event_name"], "YES 2026")
        self.assertIn("Belagavi", info["venue_address"])

        # Verify dynamic schedule items
        sched_res = self.client.get("/api/event/schedule?day=day1")
        self.assertEqual(sched_res.status_code, 200)
        items = sched_res.get_json()["schedule"]
        self.assertGreaterEqual(len(items), 1)

    def test_07_database_health_and_diagnostics(self):
        # Verify /api/health
        health_res = self.client.get("/api/health")
        self.assertEqual(health_res.status_code, 200)
        hdata = health_res.get_json()
        self.assertEqual(hdata["status"], "healthy")
        self.assertTrue(hdata["database"]["connected"])
        self.assertIn("engine", hdata["database"])

        # Verify /api/db-status
        db_res = self.client.get("/api/db-status")
        self.assertEqual(db_res.status_code, 200)
        db_data = db_res.get_json()
        self.assertTrue(db_data["connected"])
        self.assertIn("engine", db_data)

    def test_08_pdf_pass_download(self):
        # Register a test attendee
        payload = {
            "category": "participant",
            "full_name": "PDF Verification User",
            "email": "pdf.test@vtu.ac.in",
            "phone": "+91-98765-00000",
            "organization": "VTU Research Lab"
        }
        reg_res = self.client.post("/api/register", json=payload)
        self.assertEqual(reg_res.status_code, 200)
        reg_id = reg_res.get_json()["registration_id"]

        # Request PDF pass
        pdf_res = self.client.get(f"/api/registration/{reg_id}/pdf")
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.mimetype, "application/pdf")
        cd_header = pdf_res.headers.get("Content-Disposition", "")
        self.assertTrue(f"YES2026_Badge_{reg_id}.pdf" in cd_header or f"YES2026_Pass_{reg_id}.pdf" in cd_header)
        self.assertTrue(pdf_res.data.startswith(b"%PDF-"), "Generated file must be a valid vector PDF starting with %PDF- header")
        self.assertGreater(len(pdf_res.data), 1000, "PDF pass should have substantial payload")

        # Request QR Pass Card (PNG with ID)
        qr_pass_res = self.client.get(f"/api/registration/{reg_id}/qr-pass.png")
        self.assertEqual(qr_pass_res.status_code, 200)
        self.assertEqual(qr_pass_res.mimetype, "image/png")
        self.assertIn(f"YES2026_QR_Pass_{reg_id}.png", qr_pass_res.headers.get("Content-Disposition", ""))
        self.assertTrue(qr_pass_res.data.startswith(b"\x89PNG\r\n\x1a\n"), "Generated file must be a valid PNG image")

    def test_09_checkin_auth_protection(self):
        # Without admin session, /checkin must redirect to /admin
        anon_client = app.test_client()
        res = anon_client.get("/checkin")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/admin", res.headers.get("Location", ""))

        # With admin session, /checkin must allow access
        with anon_client.session_transaction() as sess:
            sess["admin_logged_in"] = True
        res_auth = anon_client.get("/checkin")
        self.assertEqual(res_auth.status_code, 200)
        self.assertIn(b"Scanner Ready", res_auth.data)

        # Verify admin dashboard contains button to redirect to kiosk and no auto-scanner script
        admin_res = anon_client.get("/admin")
        self.assertEqual(admin_res.status_code, 200)
        self.assertIn(b"/checkin", admin_res.data, "Admin dashboard must have button linking to kiosk")
        self.assertNotIn(b"/static/js/scanner.js", admin_res.data, "Admin dashboard must not load camera scanner automatically")

        # Verify public pages do not contain any kiosk buttons
        index_res = anon_client.get("/")
        self.assertNotIn(b'href="/checkin"', index_res.data, "Landing page must not expose kiosk button")
        reg_res = anon_client.get("/register")
        self.assertNotIn(b'href="/checkin"', reg_res.data, "Registration page must not expose kiosk button")

    def test_10_duplicate_email_prevention(self):
        # 1. First registration with new email
        payload1 = {
            "category": "participant",
            "full_name": "Original Registrant",
            "email": "single.use@vtu.ac.in",
            "phone": "+91-98765-00001",
            "organization": "VTU Engineering"
        }
        res1 = self.client.post("/api/register", json=payload1)
        self.assertEqual(res1.status_code, 200)
        data1 = res1.get_json()
        self.assertTrue(data1["success"])
        reg_id = data1["registration_id"]

        # 2. Second registration attempting to use identical email
        payload2 = {
            "category": "delegate",
            "full_name": "Imposter Registrant",
            "email": "single.use@vtu.ac.in",
            "phone": "+91-98765-00002",
            "organization": "Different Org"
        }
        res2 = self.client.post("/api/register", json=payload2)
        self.assertEqual(res2.status_code, 400)
        data2 = res2.get_json()
        self.assertFalse(data2["success"])
        self.assertEqual(data2.get("error_type"), "DUPLICATE_EMAIL")
        self.assertIn("already registered", data2["error"])

        # 3. Third registration with case variation (UPPERCASE)
        payload3 = dict(payload2)
        payload3["email"] = "SINGLE.USE@VTU.AC.IN"
        res3 = self.client.post("/api/register", json=payload3)
        self.assertEqual(res3.status_code, 400)
        data3 = res3.get_json()
        self.assertFalse(data3["success"])
        self.assertEqual(data3.get("error_type"), "DUPLICATE_EMAIL")

    @classmethod
    def tearDownClass(cls):
        with cls.client.session_transaction() as sess:
            sess["admin_logged_in"] = True
        cls.client.post("/api/admin/clear-all")

if __name__ == "__main__":
    unittest.main()

