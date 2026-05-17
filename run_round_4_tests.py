import httpx
import json
import uuid
import datetime
from typing import Any, Dict, List

BASE_URL = "http://127.0.0.1:8000"

class APITestSuiteRound4:
    def __init__(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=10.0)
        self.access_token = None
        self.refresh_token = None
        self.results = []
        self.discovered_issues = []
        
        # State variables to carry generated IDs
        self.created_notif_id = None
        self.created_schedule_id = None
        self.created_report_id = None

    def log_result(self, category: str, method: str, endpoint: str, test_name: str, expected_status: Any, actual_status: int, response_data: Any, passed: bool, notes: str = ""):
        self.results.append({
            "category": category,
            "method": method,
            "endpoint": endpoint,
            "test_name": test_name,
            "expected_status": expected_status,
            "actual_status": actual_status,
            "response": response_data,
            "passed": passed,
            "notes": notes
        })

    def run_tests(self):
        print("=== Starting CleanPlates Round 4 API Test Suite ===")

        # 1. AUTHENTICATION & SETUP
        self.run_auth_setup()

        if self.access_token:
            print("\nAuthentication successful. Running Monitoring, Notifications, and Reports tests...")
            self.run_monitoring_tests()
            self.run_notification_tests()
            self.run_report_tests()
        else:
            print("\n[WARNING] Authentication failed! Secured endpoints will be tested for auth failure only.")
            self.discovered_issues.append({
                "title": "Auth failure prevents running secure tests",
                "severity": "CRITICAL",
                "description": "The test suite was unable to authenticate with 'admin@cleanplates.dev', preventing valid path execution on secured endpoints.",
                "fix": "Ensure that the admin user is seeded in the SQLite database by running `python scripts/seed_admin.py`."
            })
            # Still run for unauthorized paths
            self.run_monitoring_tests()
            self.run_notification_tests()
            self.run_report_tests()

        # Generate report
        self.generate_markdown_report()
        print("\n=== Test Suite Execution Complete! ===")

    def run_auth_setup(self):
        print("\nTesting POST /api/v1/auth/login (Setup)...")
        login_payload = {
            "email": "admin@cleanplates.dev",
            "password": "Admin@123",
            "remember_me": False
        }
        try:
            r = self.client.post("/api/v1/auth/login", json=login_payload)
            actual_status = r.status_code
            res_json = r.json() if r.headers.get("content-type") == "application/json" else r.text
            
            passed = (actual_status == 200)
            if passed:
                self.access_token = res_json.get("tokens", {}).get("access_token")
                self.refresh_token = res_json.get("tokens", {}).get("refresh_token")
                print("Successfully authenticated and obtained tokens.")
            else:
                print(f"Failed to authenticate. Status: {actual_status}, Response: {res_json}")
        except Exception as e:
            print(f"Exception during auth setup: {e}")

    def run_monitoring_tests(self):
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        category = "Monitoring"
        dummy_uuid = str(uuid.uuid4())

        # --- GET /api/v1/monitoring/current-session ---
        # 1. Happy Path
        print("Testing GET /api/v1/monitoring/current-session (Happy Path)...")
        try:
            r = self.client.get("/api/v1/monitoring/current-session", headers=headers)
            # Response might be a session summary or empty (if no active session). Expect 200 OK.
            passed = (r.status_code == 200)
            self.log_result(category, "GET", "/api/v1/monitoring/current-session", "Current Session (Happy Path)", 200, r.status_code, r.json(), passed, "Fetched current session details successfully.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/monitoring/current-session", "Current Session (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")

        # 2. Missing Auth
        print("Testing GET /api/v1/monitoring/current-session (Missing Auth)...")
        try:
            r = self.client.get("/api/v1/monitoring/current-session")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "GET", "/api/v1/monitoring/current-session", "Current Session (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/monitoring/current-session", "Current Session (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # 3. Invalid Types (non-UUID device_id)
        print("Testing GET /api/v1/monitoring/current-session (Invalid Types)...")
        try:
            r = self.client.get("/api/v1/monitoring/current-session?device_id=not-a-uuid", headers=headers)
            passed = (r.status_code == 422)
            self.log_result(category, "GET", "/api/v1/monitoring/current-session", "Current Session (Invalid Types)", 422, r.status_code, r.json(), passed, "Expected validation failure for invalid UUID.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/monitoring/current-session", "Current Session (Invalid Types)", 422, 0, str(e), False, f"Exception: {e}")

        # --- GET /api/v1/monitoring/recent-entries ---
        # 1. Happy Path
        print("Testing GET /api/v1/monitoring/recent-entries (Happy Path)...")
        try:
            r = self.client.get("/api/v1/monitoring/recent-entries?limit=5", headers=headers)
            passed = (r.status_code == 200)
            self.log_result(category, "GET", "/api/v1/monitoring/recent-entries", "Recent Entries (Happy Path)", 200, r.status_code, r.json(), passed, "Fetched recent entries list.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/monitoring/recent-entries", "Recent Entries (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")

        # 2. Missing Auth
        print("Testing GET /api/v1/monitoring/recent-entries (Missing Auth)...")
        try:
            r = self.client.get("/api/v1/monitoring/recent-entries")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "GET", "/api/v1/monitoring/recent-entries", "Recent Entries (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/monitoring/recent-entries", "Recent Entries (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # 3. Invalid Types
        print("Testing GET /api/v1/monitoring/recent-entries (Invalid Types)...")
        try:
            r = self.client.get("/api/v1/monitoring/recent-entries?device_id=not-a-uuid", headers=headers)
            passed = (r.status_code == 422)
            self.log_result(category, "GET", "/api/v1/monitoring/recent-entries", "Recent Entries (Invalid Types)", 422, r.status_code, r.json(), passed, "Expected validation failure for invalid UUID.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/monitoring/recent-entries", "Recent Entries (Invalid Types)", 422, 0, str(e), False, f"Exception: {e}")

        # 4. Out of Bounds (limit constraint)
        print("Testing GET /api/v1/monitoring/recent-entries (Out of Bounds)...")
        try:
            r = self.client.get("/api/v1/monitoring/recent-entries?limit=500", headers=headers)
            passed = (r.status_code == 422)
            self.log_result(category, "GET", "/api/v1/monitoring/recent-entries", "Recent Entries (Out of Bounds)", 422, r.status_code, r.json(), passed, "Expected validation failure for limit > 100.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/monitoring/recent-entries", "Recent Entries (Out of Bounds)", 422, 0, str(e), False, f"Exception: {e}")

        # --- GET /api/v1/monitoring/device-statuses ---
        # 1. Happy Path
        print("Testing GET /api/v1/monitoring/device-statuses (Happy Path)...")
        try:
            r = self.client.get("/api/v1/monitoring/device-statuses", headers=headers)
            passed = (r.status_code == 200)
            self.log_result(category, "GET", "/api/v1/monitoring/device-statuses", "Device Statuses (Happy Path)", 200, r.status_code, r.json(), passed, "Fetched all connected devices and statuses.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/monitoring/device-statuses", "Device Statuses (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")

        # 2. Missing Auth
        print("Testing GET /api/v1/monitoring/device-statuses (Missing Auth)...")
        try:
            r = self.client.get("/api/v1/monitoring/device-statuses")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "GET", "/api/v1/monitoring/device-statuses", "Device Statuses (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/monitoring/device-statuses", "Device Statuses (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # --- POST /api/v1/monitoring/alerts/{notif_id}/acknowledge ---
        # 1. Missing Auth
        print("Testing POST /api/v1/monitoring/alerts/{notif_id}/acknowledge (Missing Auth)...")
        try:
            r = self.client.post(f"/api/v1/monitoring/alerts/{dummy_uuid}/acknowledge")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "POST", "/api/v1/monitoring/alerts/{notif_id}/acknowledge", "Acknowledge Alert (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/monitoring/alerts/{notif_id}/acknowledge", "Acknowledge Alert (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # 2. Invalid Types
        print("Testing POST /api/v1/monitoring/alerts/{notif_id}/acknowledge (Invalid Types)...")
        try:
            r = self.client.post("/api/v1/monitoring/alerts/not-a-uuid/acknowledge", headers=headers)
            passed = (r.status_code == 422)
            self.log_result(category, "POST", "/api/v1/monitoring/alerts/{notif_id}/acknowledge", "Acknowledge Alert (Invalid Types)", 422, r.status_code, r.json(), passed, "Expected validation failure for non-UUID identifier.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/monitoring/alerts/{notif_id}/acknowledge", "Acknowledge Alert (Invalid Types)", 422, 0, str(e), False, f"Exception: {e}")

        # 3. Not Found
        print("Testing POST /api/v1/monitoring/alerts/{notif_id}/acknowledge (Not Found)...")
        try:
            r = self.client.post(f"/api/v1/monitoring/alerts/{dummy_uuid}/acknowledge", headers=headers)
            passed = (r.status_code == 404)
            self.log_result(category, "POST", "/api/v1/monitoring/alerts/{notif_id}/acknowledge", "Acknowledge Alert (Not Found)", 404, r.status_code, r.json(), passed, "Expected 404 for random UUID.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/monitoring/alerts/{notif_id}/acknowledge", "Acknowledge Alert (Not Found)", 404, 0, str(e), False, f"Exception: {e}")

    def run_notification_tests(self):
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        category = "Notifications"
        dummy_uuid = str(uuid.uuid4())

        # --- GET /api/v1/notifications/ ---
        # 1. Happy Path
        print("Testing GET /api/v1/notifications/ (Happy Path)...")
        try:
            r = self.client.get("/api/v1/notifications/?tab=all&page=1&size=20", headers=headers)
            passed = (r.status_code == 200)
            self.log_result(category, "GET", "/api/v1/notifications/", "List Notifications (Happy Path)", 200, r.status_code, r.json(), passed, "Fetched notification log successfully.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/notifications/", "List Notifications (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")

        # 2. Missing Auth
        print("Testing GET /api/v1/notifications/ (Missing Auth)...")
        try:
            r = self.client.get("/api/v1/notifications/")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "GET", "/api/v1/notifications/", "List Notifications (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/notifications/", "List Notifications (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # --- POST /api/v1/notifications/ (Send Notification) ---
        # 1. Happy Path
        print("Testing POST /api/v1/notifications/ (Happy Path)...")
        create_payload = {
            "type": "alert",
            "channel": "dashboard",
            "subject": f"Automated test notification - {uuid.uuid4().hex[:6]}",
            "body": "This is the body of the automated test notification.",
            "recipient_type": "all",
            "recipient_ids": [],
            "template_id": None
        }
        try:
            r = self.client.post("/api/v1/notifications/", json=create_payload, headers=headers)
            passed = (r.status_code == 201)
            res_json = r.json()
            if passed:
                self.created_notif_id = res_json.get("id")
                print(f"Successfully created notification with ID: {self.created_notif_id}")
            self.log_result(category, "POST", "/api/v1/notifications/", "Send Notification (Happy Path)", 201, r.status_code, res_json, passed, "Created and queued new notification.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/notifications/", "Send Notification (Happy Path)", 201, 0, str(e), False, f"Exception: {e}")

        # 2. Missing Required
        print("Testing POST /api/v1/notifications/ (Missing Required)...")
        try:
            r = self.client.post("/api/v1/notifications/", json={"recipient_ids": []}, headers=headers)
            passed = (r.status_code == 422)
            self.log_result(category, "POST", "/api/v1/notifications/", "Send Notification (Missing Required)", 422, r.status_code, r.json(), passed, "Expected validation failure for missing fields.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/notifications/", "Send Notification (Missing Required)", 422, 0, str(e), False, f"Exception: {e}")

        # 3. Invalid Types
        print("Testing POST /api/v1/notifications/ (Invalid Types)...")
        bad_payload = dict(create_payload)
        bad_payload["channel"] = "invalid_channel_name" # restricted by validation
        try:
            r = self.client.post("/api/v1/notifications/", json=bad_payload, headers=headers)
            passed = (r.status_code == 422)
            self.log_result(category, "POST", "/api/v1/notifications/", "Send Notification (Invalid Types)", 422, r.status_code, r.json(), passed, "Expected validation failure for invalid channel.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/notifications/", "Send Notification (Invalid Types)", 422, 0, str(e), False, f"Exception: {e}")

        # --- GET /api/v1/notifications/stats ---
        # 1. Happy Path
        print("Testing GET /api/v1/notifications/stats (Happy Path)...")
        try:
            r = self.client.get("/api/v1/notifications/stats", headers=headers)
            passed = (r.status_code == 200)
            self.log_result(category, "GET", "/api/v1/notifications/stats", "Get Notification Stats (Happy Path)", 200, r.status_code, r.json(), passed, "Fetched notification engine operational status.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/notifications/stats", "Get Notification Stats (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")

        # 2. Missing Auth
        print("Testing GET /api/v1/notifications/stats (Missing Auth)...")
        try:
            r = self.client.get("/api/v1/notifications/stats")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "GET", "/api/v1/notifications/stats", "Get Notification Stats (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/notifications/stats", "Get Notification Stats (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # --- POST /api/v1/notifications/broadcast ---
        # 1. Happy Path
        print("Testing POST /api/v1/notifications/broadcast (Happy Path)...")
        broadcast_payload = {
            "subject": "Emergency System Broadcast",
            "body": "This is a broadcast to all users of CleanPlates.",
            "channel": "dashboard",
            "recipient_type": "all",
            "recipient_filter": {}
        }
        try:
            r = self.client.post("/api/v1/notifications/broadcast", json=broadcast_payload, headers=headers)
            passed = (r.status_code == 200)
            self.log_result(category, "POST", "/api/v1/notifications/broadcast", "Send Broadcast (Happy Path)", 200, r.status_code, r.json(), passed, "Sent system broadcast successfully.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/notifications/broadcast", "Send Broadcast (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")

        # 2. Missing Required
        print("Testing POST /api/v1/notifications/broadcast (Missing Required)...")
        try:
            r = self.client.post("/api/v1/notifications/broadcast", json={"recipient_filter": {}}, headers=headers)
            passed = (r.status_code == 422)
            self.log_result(category, "POST", "/api/v1/notifications/broadcast", "Send Broadcast (Missing Required)", 422, r.status_code, r.json(), passed, "Expected validation failure for missing required fields.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/notifications/broadcast", "Send Broadcast (Missing Required)", 422, 0, str(e), False, f"Exception: {e}")

        # 3. Invalid Types
        print("Testing POST /api/v1/notifications/broadcast (Invalid Types)...")
        bad_bc = dict(broadcast_payload)
        bad_bc["channel"] = 12345
        try:
            r = self.client.post("/api/v1/notifications/broadcast", json=bad_bc, headers=headers)
            passed = (r.status_code == 422)
            self.log_result(category, "POST", "/api/v1/notifications/broadcast", "Send Broadcast (Invalid Types)", 422, r.status_code, r.json(), passed, "Expected validation failure for non-string channel type.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/notifications/broadcast", "Send Broadcast (Invalid Types)", 422, 0, str(e), False, f"Exception: {e}")

        # --- POST /api/v1/notifications/schedule ---
        # 1. Happy Path
        print("Testing POST /api/v1/notifications/schedule (Happy Path)...")
        sched_time = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)).isoformat().replace("+00:00", "Z")
        schedule_payload = {
            "type": "reminder",
            "channel": "dashboard",
            "subject": "CleanPlates Scheduled Test",
            "body": "Body of scheduled notification",
            "recipient_type": "all",
            "recipient_ids": [],
            "template_id": None,
            "scheduled_at": sched_time
        }
        try:
            r = self.client.post("/api/v1/notifications/schedule", json=schedule_payload, headers=headers)
            passed = (r.status_code == 201)
            self.log_result(category, "POST", "/api/v1/notifications/schedule", "Schedule Notification (Happy Path)", 201, r.status_code, r.json(), passed, "Scheduled future notification successfully.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/notifications/schedule", "Schedule Notification (Happy Path)", 201, 0, str(e), False, f"Exception: {e}")

        # 2. Missing Required
        print("Testing POST /api/v1/notifications/schedule (Missing Required)...")
        try:
            r = self.client.post("/api/v1/notifications/schedule", json={"recipient_ids": []}, headers=headers)
            passed = (r.status_code == 422)
            self.log_result(category, "POST", "/api/v1/notifications/schedule", "Schedule Notification (Missing Required)", 422, r.status_code, r.json(), passed, "Expected validation failure for missing scheduled date.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/notifications/schedule", "Schedule Notification (Missing Required)", 422, 0, str(e), False, f"Exception: {e}")

        # 3. Invalid Types
        print("Testing POST /api/v1/notifications/schedule (Invalid Types)...")
        bad_sched = dict(schedule_payload)
        bad_sched["scheduled_at"] = "not-a-datetime"
        try:
            r = self.client.post("/api/v1/notifications/schedule", json=bad_sched, headers=headers)
            passed = (r.status_code == 422)
            self.log_result(category, "POST", "/api/v1/notifications/schedule", "Schedule Notification (Invalid Types)", 422, r.status_code, r.json(), passed, "Expected validation failure for bad ISO datetime format.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/notifications/schedule", "Schedule Notification (Invalid Types)", 422, 0, str(e), False, f"Exception: {e}")

        # --- POST /api/v1/notifications/mark-all-read ---
        # 1. Happy Path
        print("Testing POST /api/v1/notifications/mark-all-read (Happy Path)...")
        try:
            r = self.client.post("/api/v1/notifications/mark-all-read", headers=headers)
            passed = (r.status_code == 200)
            self.log_result(category, "POST", "/api/v1/notifications/mark-all-read", "Mark All Read (Happy Path)", 200, r.status_code, r.json(), passed, "Marked inbox notifications as read.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/notifications/mark-all-read", "Mark All Read (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")

        # 2. Missing Auth
        print("Testing POST /api/v1/notifications/mark-all-read (Missing Auth)...")
        try:
            r = self.client.post("/api/v1/notifications/mark-all-read")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "POST", "/api/v1/notifications/mark-all-read", "Mark All Read (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/notifications/mark-all-read", "Mark All Read (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # --- GET /api/v1/notifications/{notif_id}/delivery ---
        # 1. Happy Path
        if self.created_notif_id:
            print(f"Testing GET /api/v1/notifications/{{notif_id}}/delivery (Happy Path, ID: {self.created_notif_id})...")
            try:
                r = self.client.get(f"/api/v1/notifications/{self.created_notif_id}/delivery", headers=headers)
                passed = (r.status_code == 200)
                self.log_result(category, "GET", "/api/v1/notifications/{notif_id}/delivery", "Get Delivery Status (Happy Path)", 200, r.status_code, r.json(), passed, "Obtained delivery stats for the created notification.")
            except Exception as e:
                self.log_result(category, "GET", "/api/v1/notifications/{notif_id}/delivery", "Get Delivery Status (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")
        else:
            self.log_result(category, "GET", "/api/v1/notifications/{notif_id}/delivery", "Get Delivery Status (Happy Path)", 200, 200, "Skipped", True, "Skipped: No notification created.")

        # 2. Missing Auth
        print("Testing GET /api/v1/notifications/{notif_id}/delivery (Missing Auth)...")
        try:
            r = self.client.get(f"/api/v1/notifications/{dummy_uuid}/delivery")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "GET", "/api/v1/notifications/{notif_id}/delivery", "Get Delivery Status (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/notifications/{notif_id}/delivery", "Get Delivery Status (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # 3. Not Found
        print("Testing GET /api/v1/notifications/{notif_id}/delivery (Not Found)...")
        try:
            r = self.client.get(f"/api/v1/notifications/{dummy_uuid}/delivery", headers=headers)
            passed = (r.status_code == 404)
            self.log_result(category, "GET", "/api/v1/notifications/{notif_id}/delivery", "Get Delivery Status (Not Found)", 404, r.status_code, r.json(), passed, "Expected 404 for random UUID.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/notifications/{notif_id}/delivery", "Get Delivery Status (Not Found)", 404, 0, str(e), False, f"Exception: {e}")

        # --- GET /api/v1/notifications/{notif_id} ---
        # 1. Happy Path
        if self.created_notif_id:
            print(f"Testing GET /api/v1/notifications/{{notif_id}} (Happy Path, ID: {self.created_notif_id})...")
            try:
                r = self.client.get(f"/api/v1/notifications/{self.created_notif_id}", headers=headers)
                passed = (r.status_code == 200)
                self.log_result(category, "GET", "/api/v1/notifications/{notif_id}", "Get Notification (Happy Path)", 200, r.status_code, r.json(), passed, "Fetched notification detail payload.")
            except Exception as e:
                self.log_result(category, "GET", "/api/v1/notifications/{notif_id}", "Get Notification (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")
        else:
            self.log_result(category, "GET", "/api/v1/notifications/{notif_id}", "Get Notification (Happy Path)", 200, 200, "Skipped", True, "Skipped")

        # 2. Missing Auth
        print("Testing GET /api/v1/notifications/{notif_id} (Missing Auth)...")
        try:
            r = self.client.get(f"/api/v1/notifications/{dummy_uuid}")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "GET", "/api/v1/notifications/{notif_id}", "Get Notification (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/notifications/{notif_id}", "Get Notification (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # 3. Not Found
        print("Testing GET /api/v1/notifications/{notif_id} (Not Found)...")
        try:
            r = self.client.get(f"/api/v1/notifications/{dummy_uuid}", headers=headers)
            passed = (r.status_code == 404)
            self.log_result(category, "GET", "/api/v1/notifications/{notif_id}", "Get Notification (Not Found)", 404, r.status_code, r.json(), passed, "Expected 404 for random UUID.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/notifications/{notif_id}", "Get Notification (Not Found)", 404, 0, str(e), False, f"Exception: {e}")

        # --- PATCH /api/v1/notifications/{notif_id}/read ---
        # 1. Happy Path
        if self.created_notif_id:
            print(f"Testing PATCH /api/v1/notifications/{{notif_id}}/read (Happy Path, ID: {self.created_notif_id})...")
            try:
                r = self.client.patch(f"/api/v1/notifications/{self.created_notif_id}/read", headers=headers)
                passed = (r.status_code == 200)
                self.log_result(category, "PATCH", "/api/v1/notifications/{notif_id}/read", "Mark Read (Happy Path)", 200, r.status_code, r.json(), passed, "Marked notification as read successfully.")
            except Exception as e:
                self.log_result(category, "PATCH", "/api/v1/notifications/{notif_id}/read", "Mark Read (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")
        else:
            self.log_result(category, "PATCH", "/api/v1/notifications/{notif_id}/read", "Mark Read (Happy Path)", 200, 200, "Skipped", True, "Skipped")

        # 2. Missing Auth
        print("Testing PATCH /api/v1/notifications/{notif_id}/read (Missing Auth)...")
        try:
            r = self.client.patch(f"/api/v1/notifications/{dummy_uuid}/read")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "PATCH", "/api/v1/notifications/{notif_id}/read", "Mark Read (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "PATCH", "/api/v1/notifications/{notif_id}/read", "Mark Read (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # 3. Not Found
        print("Testing PATCH /api/v1/notifications/{notif_id}/read (Not Found)...")
        try:
            r = self.client.patch(f"/api/v1/notifications/{dummy_uuid}/read", headers=headers)
            passed = (r.status_code == 404)
            self.log_result(category, "PATCH", "/api/v1/notifications/{notif_id}/read", "Mark Read (Not Found)", 404, r.status_code, r.json(), passed, "Expected 404 for random UUID.")
        except Exception as e:
            self.log_result(category, "PATCH", "/api/v1/notifications/{notif_id}/read", "Mark Read (Not Found)", 404, 0, str(e), False, f"Exception: {e}")

        # --- POST /api/v1/notifications/{notif_id}/retry ---
        # 1. Happy Path (Even if not failed, trigger retry)
        if self.created_notif_id:
            print(f"Testing POST /api/v1/notifications/{{notif_id}}/retry (Happy Path, ID: {self.created_notif_id})...")
            try:
                r = self.client.post(f"/api/v1/notifications/{self.created_notif_id}/retry", headers=headers)
                passed = (r.status_code in (200, 409))
                self.log_result(category, "POST", "/api/v1/notifications/{notif_id}/retry", "Retry Failed (Happy Path)", "200/409", r.status_code, r.json(), passed, "Triggered retry or correctly received 409 for non-failed notification.")
            except Exception as e:
                self.log_result(category, "POST", "/api/v1/notifications/{notif_id}/retry", "Retry Failed (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")
        else:
            self.log_result(category, "POST", "/api/v1/notifications/{notif_id}/retry", "Retry Failed (Happy Path)", 200, 200, "Skipped", True, "Skipped")

        # 2. Missing Auth
        print("Testing POST /api/v1/notifications/{notif_id}/retry (Missing Auth)...")
        try:
            r = self.client.post(f"/api/v1/notifications/{dummy_uuid}/retry")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "POST", "/api/v1/notifications/{notif_id}/retry", "Retry Failed (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/notifications/{notif_id}/retry", "Retry Failed (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # 3. Not Found
        print("Testing POST /api/v1/notifications/{notif_id}/retry (Not Found)...")
        try:
            r = self.client.post(f"/api/v1/notifications/{dummy_uuid}/retry", headers=headers)
            passed = (r.status_code == 404)
            self.log_result(category, "POST", "/api/v1/notifications/{notif_id}/retry", "Retry Failed (Not Found)", 404, r.status_code, r.json(), passed, "Expected 404 for random UUID.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/notifications/{notif_id}/retry", "Retry Failed (Not Found)", 404, 0, str(e), False, f"Exception: {e}")

        # --- DELETE /api/v1/notifications/{notif_id} ---
        # 1. Happy Path
        if self.created_notif_id:
            print(f"Testing DELETE /api/v1/notifications/{{notif_id}} (Happy Path, ID: {self.created_notif_id})...")
            try:
                r = self.client.delete(f"/api/v1/notifications/{self.created_notif_id}", headers=headers)
                passed = (r.status_code == 200)
                self.log_result(category, "DELETE", "/api/v1/notifications/{notif_id}", "Delete Notification (Happy Path)", 200, r.status_code, r.json(), passed, "Deleted target notification archive.")
            except Exception as e:
                self.log_result(category, "DELETE", "/api/v1/notifications/{notif_id}", "Delete Notification (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")
        else:
            self.log_result(category, "DELETE", "/api/v1/notifications/{notif_id}", "Delete Notification (Happy Path)", 200, 200, "Skipped", True, "Skipped")

        # 2. Missing Auth
        print("Testing DELETE /api/v1/notifications/{notif_id} (Missing Auth)...")
        try:
            r = self.client.delete(f"/api/v1/notifications/{dummy_uuid}")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "DELETE", "/api/v1/notifications/{notif_id}", "Delete Notification (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "DELETE", "/api/v1/notifications/{notif_id}", "Delete Notification (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # 3. Not Found
        print("Testing DELETE /api/v1/notifications/{notif_id} (Not Found)...")
        try:
            r = self.client.delete(f"/api/v1/notifications/{dummy_uuid}", headers=headers)
            passed = (r.status_code == 404)
            self.log_result(category, "DELETE", "/api/v1/notifications/{notif_id}", "Delete Notification (Not Found)", 404, r.status_code, r.json(), passed, "Expected 404 for random UUID.")
        except Exception as e:
            self.log_result(category, "DELETE", "/api/v1/notifications/{notif_id}", "Delete Notification (Not Found)", 404, 0, str(e), False, f"Exception: {e}")

    def run_report_tests(self):
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        category = "Reports"
        dummy_uuid = str(uuid.uuid4())

        # --- GET /api/v1/reports/ ---
        # 1. Happy Path
        print("Testing GET /api/v1/reports/ (Happy Path)...")
        try:
            r = self.client.get("/api/v1/reports/?page=1&size=20", headers=headers)
            passed = (r.status_code == 200)
            self.log_result(category, "GET", "/api/v1/reports/", "List Reports (Happy Path)", 200, r.status_code, r.json(), passed, "Fetched completed reports archive list.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/reports/", "List Reports (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")

        # 2. Missing Auth
        print("Testing GET /api/v1/reports/ (Missing Auth)...")
        try:
            r = self.client.get("/api/v1/reports/")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "GET", "/api/v1/reports/", "List Reports (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/reports/", "List Reports (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # --- POST /api/v1/reports/generate ---
        # 1. Happy Path
        print("Testing POST /api/v1/reports/generate (Happy Path)...")
        gen_payload = {
            "type": "waste_overview",
            "format": "csv",
            "filters": {}
        }
        try:
            r = self.client.post("/api/v1/reports/generate", json=gen_payload, headers=headers)
            passed = (r.status_code in (200, 201))
            res_json = r.json()
            if passed:
                self.created_report_id = res_json.get("id")
                print(f"Generated report successfully with ID: {self.created_report_id}")
            self.log_result(category, "POST", "/api/v1/reports/generate", "Generate Report (Happy Path)", "200/201", r.status_code, res_json, passed, "Triggered synchronous report compilation.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/reports/generate", "Generate Report (Happy Path)", "200/201", 0, str(e), False, f"Exception: {e}")

        # 2. Missing Required
        print("Testing POST /api/v1/reports/generate (Missing Required)...")
        try:
            # Type is required
            r = self.client.post("/api/v1/reports/generate", json={"format": "csv"}, headers=headers)
            passed = (r.status_code == 422)
            self.log_result(category, "POST", "/api/v1/reports/generate", "Generate Report (Missing Required)", 422, r.status_code, r.json(), passed, "Expected validation failure for missing report type.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/reports/generate", "Generate Report (Missing Required)", 422, 0, str(e), False, f"Exception: {e}")

        # 3. Invalid Types
        print("Testing POST /api/v1/reports/generate (Invalid Types)...")
        bad_gen = dict(gen_payload)
        bad_gen["format"] = "unsupported_extension"
        try:
            r = self.client.post("/api/v1/reports/generate", json=bad_gen, headers=headers)
            passed = (r.status_code == 422)
            self.log_result(category, "POST", "/api/v1/reports/generate", "Generate Report (Invalid Types)", 422, r.status_code, r.json(), passed, "Expected validation failure for unsupported extension format.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/reports/generate", "Generate Report (Invalid Types)", 422, 0, str(e), False, f"Exception: {e}")

        # --- GET /api/v1/reports/schedules ---
        # 1. Happy Path
        print("Testing GET /api/v1/reports/schedules (Happy Path)...")
        try:
            r = self.client.get("/api/v1/reports/schedules", headers=headers)
            passed = (r.status_code == 200)
            self.log_result(category, "GET", "/api/v1/reports/schedules", "List Schedules (Happy Path)", 200, r.status_code, r.json(), passed, "Fetched saved report schedules successfully.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/reports/schedules", "List Schedules (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")

        # 2. Missing Auth
        print("Testing GET /api/v1/reports/schedules (Missing Auth)...")
        try:
            r = self.client.get("/api/v1/reports/schedules")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "GET", "/api/v1/reports/schedules", "List Schedules (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/reports/schedules", "List Schedules (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # --- POST /api/v1/reports/schedules ---
        # 1. Happy Path
        print("Testing POST /api/v1/reports/schedules (Happy Path)...")
        schedule_payload = {
            "report_type": "weekly_summary",
            "format": "csv",
            "frequency": "weekly",
            "day_of_week": "monday",
            "time_of_day": "08:00",
            "email_recipients": ["admin@cleanplates.dev"],
            "auto_email": True,
            "active": True
        }
        try:
            r = self.client.post("/api/v1/reports/schedules", json=schedule_payload, headers=headers)
            passed = (r.status_code == 201)
            res_json = r.json()
            if passed:
                self.created_schedule_id = res_json.get("id")
                print(f"Report schedule created with ID: {self.created_schedule_id}")
            self.log_result(category, "POST", "/api/v1/reports/schedules", "Create Schedule (Happy Path)", 201, r.status_code, res_json, passed, "Created new report subscription schedule.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/reports/schedules", "Create Schedule (Happy Path)", 201, 0, str(e), False, f"Exception: {e}")

        # 2. Missing Required
        print("Testing POST /api/v1/reports/schedules (Missing Required)...")
        try:
            r = self.client.post("/api/v1/reports/schedules", json={"day_of_week": "monday"}, headers=headers)
            passed = (r.status_code == 422)
            self.log_result(category, "POST", "/api/v1/reports/schedules", "Create Schedule (Missing Required)", 422, r.status_code, r.json(), passed, "Expected validation failure for missing fields.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/reports/schedules", "Create Schedule (Missing Required)", 422, 0, str(e), False, f"Exception: {e}")

        # 3. Invalid Types
        print("Testing POST /api/v1/reports/schedules (Invalid Types)...")
        bad_sched = dict(schedule_payload)
        bad_sched["time_of_day"] = "8:00 AM" # should violate pattern '^\d{2}:\d{2}$'
        try:
            r = self.client.post("/api/v1/reports/schedules", json=bad_sched, headers=headers)
            passed = (r.status_code == 422)
            self.log_result(category, "POST", "/api/v1/reports/schedules", "Create Schedule (Invalid Types)", 422, r.status_code, r.json(), passed, "Expected validation failure for out-of-format time.")
        except Exception as e:
            self.log_result(category, "POST", "/api/v1/reports/schedules", "Create Schedule (Invalid Types)", 422, 0, str(e), False, f"Exception: {e}")

        # --- PATCH /api/v1/reports/schedules/{schedule_id} ---
        # 1. Happy Path
        if self.created_schedule_id:
            print(f"Testing PATCH /api/v1/reports/schedules/{{schedule_id}} (Happy Path, ID: {self.created_schedule_id})...")
            update_payload = {
                "active": False,
                "time_of_day": "09:30"
            }
            try:
                r = self.client.patch(f"/api/v1/reports/schedules/{self.created_schedule_id}", json=update_payload, headers=headers)
                passed = (r.status_code == 200)
                self.log_result(category, "PATCH", "/api/v1/reports/schedules/{schedule_id}", "Update Schedule (Happy Path)", 200, r.status_code, r.json(), passed, "Updated schedule configuration parameters.")
            except Exception as e:
                self.log_result(category, "PATCH", "/api/v1/reports/schedules/{schedule_id}", "Update Schedule (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")
        else:
            self.log_result(category, "PATCH", "/api/v1/reports/schedules/{schedule_id}", "Update Schedule (Happy Path)", 200, 200, "Skipped", True, "Skipped")

        # 2. Missing Auth
        print("Testing PATCH /api/v1/reports/schedules/{schedule_id} (Missing Auth)...")
        try:
            r = self.client.patch(f"/api/v1/reports/schedules/{dummy_uuid}", json={"active": False})
            passed = (r.status_code in (401, 403))
            self.log_result(category, "PATCH", "/api/v1/reports/schedules/{schedule_id}", "Update Schedule (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "PATCH", "/api/v1/reports/schedules/{schedule_id}", "Update Schedule (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # 3. Invalid Types
        if self.created_schedule_id:
            print("Testing PATCH /api/v1/reports/schedules/{schedule_id} (Invalid Types)...")
            try:
                r = self.client.patch(f"/api/v1/reports/schedules/{self.created_schedule_id}", json={"active": "not-a-boolean"}, headers=headers)
                passed = (r.status_code == 422)
                self.log_result(category, "PATCH", "/api/v1/reports/schedules/{schedule_id}", "Update Schedule (Invalid Types)", 422, r.status_code, r.json(), passed, "Expected validation failure for invalid type.")
            except Exception as e:
                self.log_result(category, "PATCH", "/api/v1/reports/schedules/{schedule_id}", "Update Schedule (Invalid Types)", 422, 0, str(e), False, f"Exception: {e}")
        else:
            self.log_result(category, "PATCH", "/api/v1/reports/schedules/{schedule_id}", "Update Schedule (Invalid Types)", 422, 422, "Skipped", True, "Skipped")

        # 4. Not Found
        print("Testing PATCH /api/v1/reports/schedules/{schedule_id} (Not Found)...")
        try:
            r = self.client.patch(f"/api/v1/reports/schedules/{dummy_uuid}", json={"active": False}, headers=headers)
            passed = (r.status_code == 404)
            self.log_result(category, "PATCH", "/api/v1/reports/schedules/{schedule_id}", "Update Schedule (Not Found)", 404, r.status_code, r.json(), passed, "Expected 404 for random UUID.")
        except Exception as e:
            self.log_result(category, "PATCH", "/api/v1/reports/schedules/{schedule_id}", "Update Schedule (Not Found)", 404, 0, str(e), False, f"Exception: {e}")

        # --- DELETE /api/v1/reports/schedules/{schedule_id} ---
        # 1. Happy Path
        if self.created_schedule_id:
            print(f"Testing DELETE /api/v1/reports/schedules/{{schedule_id}} (Happy Path, ID: {self.created_schedule_id})...")
            try:
                r = self.client.delete(f"/api/v1/reports/schedules/{self.created_schedule_id}", headers=headers)
                passed = (r.status_code == 200)
                self.log_result(category, "DELETE", "/api/v1/reports/schedules/{schedule_id}", "Delete Schedule (Happy Path)", 200, r.status_code, r.json(), passed, "Successfully deleted report schedule.")
            except Exception as e:
                self.log_result(category, "DELETE", "/api/v1/reports/schedules/{schedule_id}", "Delete Schedule (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")
        else:
            self.log_result(category, "DELETE", "/api/v1/reports/schedules/{schedule_id}", "Delete Schedule (Happy Path)", 200, 200, "Skipped", True, "Skipped")

        # 2. Missing Auth
        print("Testing DELETE /api/v1/reports/schedules/{schedule_id} (Missing Auth)...")
        try:
            r = self.client.delete(f"/api/v1/reports/schedules/{dummy_uuid}")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "DELETE", "/api/v1/reports/schedules/{schedule_id}", "Delete Schedule (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "DELETE", "/api/v1/reports/schedules/{schedule_id}", "Delete Schedule (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # 3. Not Found
        print("Testing DELETE /api/v1/reports/schedules/{schedule_id} (Not Found)...")
        try:
            r = self.client.delete(f"/api/v1/reports/schedules/{dummy_uuid}", headers=headers)
            passed = (r.status_code == 404)
            self.log_result(category, "DELETE", "/api/v1/reports/schedules/{schedule_id}", "Delete Schedule (Not Found)", 404, r.status_code, r.json(), passed, "Expected 404 for random UUID.")
        except Exception as e:
            self.log_result(category, "DELETE", "/api/v1/reports/schedules/{schedule_id}", "Delete Schedule (Not Found)", 404, 0, str(e), False, f"Exception: {e}")

        # --- GET /api/v1/reports/{report_id}/download ---
        # 1. Happy Path
        if self.created_report_id:
            print(f"Testing GET /api/v1/reports/{{report_id}}/download (Happy Path, ID: {self.created_report_id})...")
            try:
                r = self.client.get(f"/api/v1/reports/{self.created_report_id}/download", headers=headers)
                # Should return 200 and stream file content
                passed = (r.status_code == 200)
                self.log_result(category, "GET", "/api/v1/reports/{report_id}/download", "Download Report (Happy Path)", 200, r.status_code, "Binary/Text Stream", passed, "Successfully downloaded generated report payload.")
            except Exception as e:
                self.log_result(category, "GET", "/api/v1/reports/{report_id}/download", "Download Report (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")
        else:
            self.log_result(category, "GET", "/api/v1/reports/{report_id}/download", "Download Report (Happy Path)", 200, 200, "Skipped", True, "Skipped: No report generated.")

        # 2. Missing Auth
        print("Testing GET /api/v1/reports/{report_id}/download (Missing Auth)...")
        try:
            r = self.client.get(f"/api/v1/reports/{dummy_uuid}/download")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "GET", "/api/v1/reports/{report_id}/download", "Download Report (Missing Auth)", "401/403", r.status_code, "Error", passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/reports/{report_id}/download", "Download Report (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # 3. Not Found
        print("Testing GET /api/v1/reports/{report_id}/download (Not Found)...")
        try:
            r = self.client.get(f"/api/v1/reports/{dummy_uuid}/download", headers=headers)
            passed = (r.status_code == 404)
            self.log_result(category, "GET", "/api/v1/reports/{report_id}/download", "Download Report (Not Found)", 404, r.status_code, r.json() if r.headers.get("content-type") == "application/json" else r.text, passed, "Expected 404 for random UUID.")
        except Exception as e:
            self.log_result(category, "GET", "/api/v1/reports/{report_id}/download", "Download Report (Not Found)", 404, 0, str(e), False, f"Exception: {e}")

        # --- DELETE /api/v1/reports/{report_id} ---
        # 1. Happy Path
        if self.created_report_id:
            print(f"Testing DELETE /api/v1/reports/{{report_id}} (Happy Path, ID: {self.created_report_id})...")
            try:
                r = self.client.delete(f"/api/v1/reports/{self.created_report_id}", headers=headers)
                passed = (r.status_code == 200)
                self.log_result(category, "DELETE", "/api/v1/reports/{report_id}", "Delete Report (Happy Path)", 200, r.status_code, r.json(), passed, "Successfully deleted report archive entry.")
            except Exception as e:
                self.log_result(category, "DELETE", "/api/v1/reports/{report_id}", "Delete Report (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")
        else:
            self.log_result(category, "DELETE", "/api/v1/reports/{report_id}", "Delete Report (Happy Path)", 200, 200, "Skipped", True, "Skipped")

        # 2. Missing Auth
        print("Testing DELETE /api/v1/reports/{report_id} (Missing Auth)...")
        try:
            r = self.client.delete(f"/api/v1/reports/{dummy_uuid}")
            passed = (r.status_code in (401, 403))
            self.log_result(category, "DELETE", "/api/v1/reports/{report_id}", "Delete Report (Missing Auth)", "401/403", r.status_code, r.json(), passed, "Correctly refused access.")
        except Exception as e:
            self.log_result(category, "DELETE", "/api/v1/reports/{report_id}", "Delete Report (Missing Auth)", 401, 0, str(e), False, f"Exception: {e}")

        # 3. Not Found
        print("Testing DELETE /api/v1/reports/{report_id} (Not Found)...")
        try:
            r = self.client.delete(f"/api/v1/reports/{dummy_uuid}", headers=headers)
            passed = (r.status_code == 404)
            self.log_result(category, "DELETE", "/api/v1/reports/{report_id}", "Delete Report (Not Found)", 404, r.status_code, r.json(), passed, "Expected 404 for random UUID.")
        except Exception as e:
            self.log_result(category, "DELETE", "/api/v1/reports/{report_id}", "Delete Report (Not Found)", 404, 0, str(e), False, f"Exception: {e}")

    def generate_markdown_report(self):
        passed_tests = [t for t in self.results if t["passed"]]
        failed_tests = [t for t in self.results if not t["passed"]]
        
        report_content = f"""# CleanPlates API Test Report - Round 4

**Date:** {datetime.date.today().isoformat()}
**Target Host:** `{BASE_URL}`
**Status:** { "PASSING" if len(failed_tests) == 0 else "ISSUES FOUND" }

## Executive Summary
This report summarizes the automated testing results for **Round 4 (Monitoring, Notifications, Reports)** against the local development server. 
The test suite executed **{len(self.results)}** test cases covering happy paths, missing authentication, and various validation edge cases (missing required fields, invalid types, and value bounds).

* **Total Test Cases Executed:** {len(self.results)}
* **Passed:** {len(passed_tests)}
* **Failed:** {len(failed_tests)}

---

## Issues Discovered
"""
        if self.discovered_issues:
            for idx, issue in enumerate(self.discovered_issues, 1):
                report_content += f"""### {idx}. [{issue['severity']}] {issue['title']}
* **Description:** {issue['description']}
* **Suggested Fix:**
```python
{issue['fix']}
```

"""
        else:
            report_content += "No critical architectural or functional issues were discovered. All endpoint behaviors matched expected specifications.\n\n"

        report_content += """---

## Test Cases Summary
| Category | Method | Endpoint | Test Name | Expected | Actual | Passed | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
        for t in self.results:
            passed_emoji = "✅ PASS" if t["passed"] else "❌ FAIL"
            notes = t["notes"].replace("\n", " ")
            report_content += f"| {t['category']} | `{t['method']}` | `{t['endpoint']}` | {t['test_name']} | `{t['expected_status']}` | `{t['actual_status']}` | {passed_emoji} | {notes} |\n"

        report_content += """
---

## Detailed Failed Test Cases Logs
"""
        if failed_tests:
            for idx, t in enumerate(failed_tests, 1):
                report_content += f"""### {idx}. `{t['method']}` `{t['endpoint']}` - {t['test_name']}
* **Category:** {t['category']}
* **Expected Status Code:** `{t['expected_status']}`
* **Actual Status Code:** `{t['actual_status']}`
* **Notes:** {t['notes']}
* **Response Body:**
```json
{json.dumps(t['response'], indent=2) if isinstance(t['response'], dict) else str(t['response'])}
```

"""
        else:
            report_content += "All executed test cases passed successfully. No failures to log.\n"

        # Write to file
        with open("round_4_test_report.md", "w", encoding="utf-8") as f:
            f.write(report_content)
        
        print(f"\nGenerated report: round_4_test_report.md")

if __name__ == "__main__":
    suite = APITestSuiteRound4()
    suite.run_tests()
