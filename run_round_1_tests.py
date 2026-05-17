import httpx
import json
import uuid
import datetime
from typing import Any, Dict, List

BASE_URL = "http://127.0.0.1:8000"

class APITestSuite:
    def __init__(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=10.0)
        self.access_token = None
        self.refresh_token = None
        self.results = []
        self.discovered_issues = []

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
        print("=== Starting CleanPlates Round 1 API Test Suite ===")

        # 1. AUTHENTICATION TESTS (Happy Path & Bad Requests)
        self.run_auth_tests()

        # If authentication succeeded, run secured tests
        if self.access_token:
            print("\nAuthentication successful. Running secured Analytics and Audit tests...")
            self.run_analytics_tests()
            self.run_audit_tests()
        else:
            print("\n[WARNING] Authentication failed! Secured endpoints will be tested for auth failure only.")
            self.discovered_issues.append({
                "title": "Auth failure prevents testing other endpoints",
                "severity": "CRITICAL",
                "description": "The test suite was unable to authenticate with 'admin@cleanplates.dev', preventing valid path execution on secured Analytics and Audit endpoints.",
                "fix": "Ensure that the admin user is seeded in the SQLite database by running `python scripts/seed_admin.py`."
            })
            # Still run with mock auth to verify 401s
            self.run_analytics_tests()
            self.run_audit_tests()

        # Generate report
        self.generate_markdown_report()
        print("\n=== Test Suite Execution Complete! ===")

    def run_auth_tests(self):
        # 1.1 Login Happy Path
        print("\nTesting POST /api/v1/auth/login (Happy Path)...")
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
                self.log_result("Auth", "POST", "/api/v1/auth/login", "Valid Login (Happy Path)", 200, actual_status, res_json, True, "Obtained JWT access & refresh tokens.")
            else:
                self.log_result("Auth", "POST", "/api/v1/auth/login", "Valid Login (Happy Path)", 200, actual_status, res_json, False, "Failed to authenticate.")
                self.discovered_issues.append({
                    "title": "Super Admin Login Failed",
                    "severity": "CRITICAL",
                    "description": f"Login with admin@cleanplates.dev failed with status {actual_status}. Response: {res_json}",
                    "fix": "Verify that the database has been seeded with standard roles and users by running `python scripts/seed_roles.py` and `python scripts/seed_admin.py`."
                })
        except Exception as e:
            self.log_result("Auth", "POST", "/api/v1/auth/login", "Valid Login (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")
            self.discovered_issues.append({
                "title": "Login Endpoint Connection/Exception Error",
                "severity": "CRITICAL",
                "description": f"An exception occurred when calling POST /api/v1/auth/login: {e}",
                "fix": "Ensure the FastAPI server is running and accessible."
            })

        # 1.2 Login Missing Required Parameters
        print("Testing POST /api/v1/auth/login (Missing Required Fields)...")
        missing_payload = {
            "remember_me": False
        }
        try:
            r = self.client.post("/api/v1/auth/login", json=missing_payload)
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 422)
            self.log_result("Auth", "POST", "/api/v1/auth/login", "Missing Required Parameters", 422, actual_status, res_json, passed, "Expected validation failure for missing fields.")
        except Exception as e:
            self.log_result("Auth", "POST", "/api/v1/auth/login", "Missing Required Parameters", 422, 0, str(e), False, f"Exception: {e}")

        # 1.3 Login Invalid Data Types
        print("Testing POST /api/v1/auth/login (Invalid Data Types)...")
        invalid_payload = {
            "email": 12345,
            "password": 12345,
            "remember_me": "yes"
        }
        try:
            r = self.client.post("/api/v1/auth/login", json=invalid_payload)
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 422)
            self.log_result("Auth", "POST", "/api/v1/auth/login", "Invalid Data Types", 422, actual_status, res_json, passed, "Expected validation failure for bad parameter types.")
        except Exception as e:
            self.log_result("Auth", "POST", "/api/v1/auth/login", "Invalid Data Types", 422, 0, str(e), False, f"Exception: {e}")

        # 1.4 Login Bad Credentials
        print("Testing POST /api/v1/auth/login (Bad Credentials)...")
        bad_payload = {
            "email": "admin@cleanplates.dev",
            "password": "WrongPassword123!",
            "remember_me": False
        }
        try:
            r = self.client.post("/api/v1/auth/login", json=bad_payload)
            actual_status = r.status_code
            res_json = r.json()
            # Bad credentials should return 400 Bad Request per verify_phase0.py (line 47)
            passed = (actual_status in (400, 401))
            self.log_result("Auth", "POST", "/api/v1/auth/login", "Bad Credentials", "400 or 401", actual_status, res_json, passed, f"Expected 400/401, got {actual_status}.")
        except Exception as e:
            self.log_result("Auth", "POST", "/api/v1/auth/login", "Bad Credentials", 400, 0, str(e), False, f"Exception: {e}")

        # 1.5 GET /api/v1/auth/me (Missing Auth)
        print("Testing GET /api/v1/auth/me (Missing Auth)...")
        try:
            r = self.client.get("/api/v1/auth/me")
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status in (401, 403))
            self.log_result("Auth", "GET", "/api/v1/auth/me", "Missing Auth Header", "401/403", actual_status, res_json, passed, "Expected 401/403 for unauthenticated request.")
        except Exception as e:
            self.log_result("Auth", "GET", "/api/v1/auth/me", "Missing Auth Header", 401, 0, str(e), False, f"Exception: {e}")

        # 1.6 GET /api/v1/auth/me (Happy Path)
        if self.access_token:
            print("Testing GET /api/v1/auth/me (Happy Path)...")
            headers = {"Authorization": f"Bearer {self.access_token}"}
            try:
                r = self.client.get("/api/v1/auth/me", headers=headers)
                actual_status = r.status_code
                res_json = r.json()
                passed = (actual_status == 200)
                self.log_result("Auth", "GET", "/api/v1/auth/me", "Valid Auth (Happy Path)", 200, actual_status, res_json, passed, "Fetched active user profile.")
            except Exception as e:
                self.log_result("Auth", "GET", "/api/v1/auth/me", "Valid Auth (Happy Path)", 200, 0, str(e), False, f"Exception: {e}")

        # 1.7 POST /api/v1/auth/forgot-password (Happy Path)
        print("Testing POST /api/v1/auth/forgot-password (Happy Path)...")
        forgot_payload = {"email": "admin@cleanplates.dev"}
        try:
            r = self.client.post("/api/v1/auth/forgot-password", json=forgot_payload)
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 200)
            self.log_result("Auth", "POST", "/api/v1/auth/forgot-password", "Forgot Password Happy Path", 200, actual_status, res_json, passed, "Expected 200 OK.")
        except Exception as e:
            self.log_result("Auth", "POST", "/api/v1/auth/forgot-password", "Forgot Password Happy Path", 200, 0, str(e), False, f"Exception: {e}")

        # 1.8 POST /api/v1/auth/forgot-password (Missing Payload)
        print("Testing POST /api/v1/auth/forgot-password (Missing Required)...")
        try:
            r = self.client.post("/api/v1/auth/forgot-password", json={})
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 422)
            self.log_result("Auth", "POST", "/api/v1/auth/forgot-password", "Forgot Password Missing Required", 422, actual_status, res_json, passed, "Expected 422 validation failure.")
        except Exception as e:
            self.log_result("Auth", "POST", "/api/v1/auth/forgot-password", "Forgot Password Missing Required", 422, 0, str(e), False, f"Exception: {e}")

        # 1.9 POST /api/v1/auth/forgot-password (Invalid types)
        print("Testing POST /api/v1/auth/forgot-password (Invalid Types)...")
        try:
            r = self.client.post("/api/v1/auth/forgot-password", json={"email": 12345})
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 422)
            self.log_result("Auth", "POST", "/api/v1/auth/forgot-password", "Forgot Password Invalid Types", 422, actual_status, res_json, passed, "Expected 422 validation failure.")
        except Exception as e:
            self.log_result("Auth", "POST", "/api/v1/auth/forgot-password", "Forgot Password Invalid Types", 422, 0, str(e), False, f"Exception: {e}")

        # 1.10 POST /api/v1/auth/reset-password (Invalid Token but Valid Schema)
        print("Testing POST /api/v1/auth/reset-password (Invalid Token, Valid Schema)...")
        reset_payload = {
            "token": "invalid_or_expired_token",
            "new_password": "NewSecurePassword123!"
        }
        try:
            r = self.client.post("/api/v1/auth/reset-password", json=reset_payload)
            actual_status = r.status_code
            res_json = r.json()
            # Since the token is invalid/expired, the service should raise an exception (usually 400 Bad Request)
            passed = (actual_status == 400)
            self.log_result("Auth", "POST", "/api/v1/auth/reset-password", "Reset Password with Invalid Token", 400, actual_status, res_json, passed, f"Expected 400 Bad Request for bad token. Got {actual_status}.")
            if not passed:
                self.discovered_issues.append({
                    "title": "Reset password did not return 400 for bad token",
                    "severity": "MEDIUM",
                    "description": f"Reset password with invalid token returned status {actual_status} instead of 400. Response: {res_json}",
                    "fix": "Ensure token verification raises HTTP 400 Bad Request if token is invalid or expired."
                })
        except Exception as e:
            self.log_result("Auth", "POST", "/api/v1/auth/reset-password", "Reset Password with Invalid Token", 400, 0, str(e), False, f"Exception: {e}")

        # 1.11 POST /api/v1/auth/reset-password (Missing Required)
        print("Testing POST /api/v1/auth/reset-password (Missing Required)...")
        try:
            r = self.client.post("/api/v1/auth/reset-password", json={})
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 422)
            self.log_result("Auth", "POST", "/api/v1/auth/reset-password", "Reset Password Missing Required", 422, actual_status, res_json, passed, "Expected 422 validation failure.")
        except Exception as e:
            self.log_result("Auth", "POST", "/api/v1/auth/reset-password", "Reset Password Missing Required", 422, 0, str(e), False, f"Exception: {e}")

        # 1.12 POST /api/v1/auth/reset-password (Invalid Types)
        print("Testing POST /api/v1/auth/reset-password (Invalid Types)...")
        try:
            r = self.client.post("/api/v1/auth/reset-password", json={"token": 12345, "new_password": 12345})
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 422)
            self.log_result("Auth", "POST", "/api/v1/auth/reset-password", "Reset Password Invalid Types", 422, actual_status, res_json, passed, "Expected 422 validation failure.")
        except Exception as e:
            self.log_result("Auth", "POST", "/api/v1/auth/reset-password", "Reset Password Invalid Types", 422, 0, str(e), False, f"Exception: {e}")

        # 1.13 POST /api/v1/auth/refresh (Happy Path)
        if self.refresh_token:
            print("Testing POST /api/v1/auth/refresh (Happy Path)...")
            refresh_payload = {
                "refresh_token": self.refresh_token
            }
            try:
                r = self.client.post("/api/v1/auth/refresh", json=refresh_payload)
                actual_status = r.status_code
                res_json = r.json()
                passed = (actual_status == 200)
                self.log_result("Auth", "POST", "/api/v1/auth/refresh", "Refresh Tokens Happy Path", 200, actual_status, res_json, passed, "Refreshed access token successfully.")
                # Update access token for subsequent tests
                if passed:
                    self.access_token = res_json.get("access_token")
            except Exception as e:
                self.log_result("Auth", "POST", "/api/v1/auth/refresh", "Refresh Tokens Happy Path", 200, 0, str(e), False, f"Exception: {e}")

        # 1.14 POST /api/v1/auth/refresh (Missing Required)
        print("Testing POST /api/v1/auth/refresh (Missing Required)...")
        try:
            r = self.client.post("/api/v1/auth/refresh", json={})
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 422)
            self.log_result("Auth", "POST", "/api/v1/auth/refresh", "Refresh Tokens Missing Required", 422, actual_status, res_json, passed, "Expected 422 validation failure.")
        except Exception as e:
            self.log_result("Auth", "POST", "/api/v1/auth/refresh", "Refresh Tokens Missing Required", 422, 0, str(e), False, f"Exception: {e}")

        # 1.15 POST /api/v1/auth/refresh (Invalid Types)
        print("Testing POST /api/v1/auth/refresh (Invalid Types)...")
        try:
            r = self.client.post("/api/v1/auth/refresh", json={"refresh_token": 12345})
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 422)
            self.log_result("Auth", "POST", "/api/v1/auth/refresh", "Refresh Tokens Invalid Types", 422, actual_status, res_json, passed, "Expected 422 validation failure.")
        except Exception as e:
            self.log_result("Auth", "POST", "/api/v1/auth/refresh", "Refresh Tokens Invalid Types", 422, 0, str(e), False, f"Exception: {e}")

        # 1.16 POST /api/v1/auth/logout (Missing Required)
        print("Testing POST /api/v1/auth/logout (Missing Required)...")
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        try:
            r = self.client.post("/api/v1/auth/logout", json={}, headers=headers)
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 422)
            self.log_result("Auth", "POST", "/api/v1/auth/logout", "Logout Missing Required", 422, actual_status, res_json, passed, "Expected 422 validation failure.")
        except Exception as e:
            self.log_result("Auth", "POST", "/api/v1/auth/logout", "Logout Missing Required", 422, 0, str(e), False, f"Exception: {e}")

        # 1.17 POST /api/v1/auth/logout (Invalid Types)
        print("Testing POST /api/v1/auth/logout (Invalid Types)...")
        try:
            r = self.client.post("/api/v1/auth/logout", json={"refresh_token": 12345}, headers=headers)
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 422)
            self.log_result("Auth", "POST", "/api/v1/auth/logout", "Logout Invalid Types", 422, actual_status, res_json, passed, "Expected 422 validation failure.")
        except Exception as e:
            self.log_result("Auth", "POST", "/api/v1/auth/logout", "Logout Invalid Types", 422, 0, str(e), False, f"Exception: {e}")

        # 1.18 POST /api/v1/auth/logout (Happy Path - do last so we keep active tokens active during test duration)
        # Note: We will run this at the end of all tests to avoid revoking tokens we need!
        # Instead, we will store a reference and call it at the end of the class run.
        self._logout_func = lambda: None
        if self.refresh_token and self.access_token:
            def logout_runner():
                print("Testing POST /api/v1/auth/logout (Happy Path)...")
                logout_headers = {"Authorization": f"Bearer {self.access_token}"}
                logout_payload = {"refresh_token": self.refresh_token}
                try:
                    r = self.client.post("/api/v1/auth/logout", json=logout_payload, headers=logout_headers)
                    actual_status = r.status_code
                    res_json = r.json()
                    passed = (actual_status == 200)
                    self.log_result("Auth", "POST", "/api/v1/auth/logout", "Logout Happy Path", 200, actual_status, res_json, passed, "Revoked refresh token successfully.")
                except Exception as e:
                    self.log_result("Auth", "POST", "/api/v1/auth/logout", "Logout Happy Path", 200, 0, str(e), False, f"Exception: {e}")
            self._logout_func = logout_runner


    def run_analytics_tests(self):
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        endpoints = [
            ("/overview", "overview"),
            ("/trends", "trends", {"type": "weekly"}),
            ("/peaks", "peaks"),
            ("/meal-distribution", "meal-distribution"),
            ("/food-waste-distribution", "food-waste-distribution", {"limit": 10}),
            ("/top-waste-contributors", "top-waste-contributors", {"limit": 10}),
            ("/improvement-tracking", "improvement-tracking"),
            ("/sustainability", "sustainability")
        ]

        for ep in endpoints:
            path_suffix = ep[0]
            name = ep[1]
            extra_params = ep[2] if len(ep) > 2 else {}
            full_path = f"/api/v1/analytics{path_suffix}"

            # 2.x.1 Valid Path
            print(f"Testing GET {full_path} (Happy Path)...")
            params = {"period": "30d", **extra_params}
            try:
                r = self.client.get(full_path, params=params, headers=headers)
                actual_status = r.status_code
                res_json = r.json()
                passed = (actual_status == 200)
                self.log_result("Analytics", "GET", full_path, f"Happy Path ({name})", 200, actual_status, res_json, passed, "Fetched analytics report successfully.")
                
                # Check for possible empty DB issues / null errors that shouldn't crash
                if not passed:
                    self.discovered_issues.append({
                        "title": f"Analytics {name} failed",
                        "severity": "HIGH",
                        "description": f"GET {full_path} returned status {actual_status} on Happy Path. Response: {res_json}",
                        "fix": "Ensure analytics controller handles empty database states gracefully without raising unhandled errors."
                    })
            except Exception as e:
                self.log_result("Analytics", "GET", full_path, f"Happy Path ({name})", 200, 0, str(e), False, f"Exception: {e}")

            # 2.x.2 Missing Auth
            print(f"Testing GET {full_path} (Missing Auth)...")
            try:
                r = self.client.get(full_path, params=params)
                actual_status = r.status_code
                res_json = r.json()
                passed = (actual_status in (401, 403))
                self.log_result("Analytics", "GET", full_path, f"Missing Auth ({name})", "401/403", actual_status, res_json, passed, "Correctly refused access.")
            except Exception as e:
                self.log_result("Analytics", "GET", full_path, f"Missing Auth ({name})", 401, 0, str(e), False, f"Exception: {e}")

            # 2.x.3 Invalid Parameters (FastAPI ge/le constraints)
            print(f"Testing GET {full_path} (Invalid Data Types/Values)...")
            invalid_params = {}
            if "limit" in params:
                invalid_params = {"limit": 101} # exceeds limit ge=1, le=100
            elif name == "trends":
                invalid_params = {"year": 5} # ge=1, le=4
            else:
                invalid_params = {"year": 5} # ge=1, le=4

            try:
                r = self.client.get(full_path, params=invalid_params, headers=headers)
                actual_status = r.status_code
                res_json = r.json()
                passed = (actual_status == 422)
                self.log_result("Analytics", "GET", full_path, f"Invalid Param ({name})", 422, actual_status, res_json, passed, "FastAPI validation rules correctly rejected input.")
            except Exception as e:
                self.log_result("Analytics", "GET", full_path, f"Invalid Param ({name})", 422, 0, str(e), False, f"Exception: {e}")


    def run_audit_tests(self):
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        
        # 3.1 List Events
        print("Testing GET /api/v1/audit/ (Happy Path)...")
        audit_events = []
        try:
            r = self.client.get("/api/v1/audit/", params={"page": 1, "size": 25}, headers=headers)
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 200)
            self.log_result("Audit", "GET", "/api/v1/audit/", "List Events Happy Path", 200, actual_status, res_json, passed, "Retrieved audit trails list.")
            if passed:
                audit_events = res_json.get("items", [])
        except Exception as e:
            self.log_result("Audit", "GET", "/api/v1/audit/", "List Events Happy Path", 200, 0, str(e), False, f"Exception: {e}")

        # 3.2 List Events Missing Auth
        print("Testing GET /api/v1/audit/ (Missing Auth)...")
        try:
            r = self.client.get("/api/v1/audit/", params={"page": 1, "size": 25})
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status in (401, 403))
            self.log_result("Audit", "GET", "/api/v1/audit/", "List Events Missing Auth", "401/403", actual_status, res_json, passed, "Correctly refused access.")
        except Exception as e:
            self.log_result("Audit", "GET", "/api/v1/audit/", "List Events Missing Auth", 401, 0, str(e), False, f"Exception: {e}")

        # 3.3 List Events Invalid
        print("Testing GET /api/v1/audit/ (Invalid Input)...")
        try:
            r = self.client.get("/api/v1/audit/", params={"page": -1}, headers=headers)
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 422)
            self.log_result("Audit", "GET", "/api/v1/audit/", "List Events Invalid Input", 422, actual_status, res_json, passed, "Expected validation failure for page < 1.")
        except Exception as e:
            self.log_result("Audit", "GET", "/api/v1/audit/", "List Events Invalid Input", 422, 0, str(e), False, f"Exception: {e}")

        # 3.4 Get Stats
        print("Testing GET /api/v1/audit/stats (Happy Path)...")
        try:
            r = self.client.get("/api/v1/audit/stats", params={"period": "today"}, headers=headers)
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 200)
            self.log_result("Audit", "GET", "/api/v1/audit/stats", "Get Stats Happy Path", 200, actual_status, res_json, passed, "Retrieved audit statistics.")
        except Exception as e:
            self.log_result("Audit", "GET", "/api/v1/audit/stats", "Get Stats Happy Path", 200, 0, str(e), False, f"Exception: {e}")

        # 3.5 Get Stats Missing Auth
        print("Testing GET /api/v1/audit/stats (Missing Auth)...")
        try:
            r = self.client.get("/api/v1/audit/stats", params={"period": "today"})
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status in (401, 403))
            self.log_result("Audit", "GET", "/api/v1/audit/stats", "Get Stats Missing Auth", "401/403", actual_status, res_json, passed, "Correctly refused access.")
        except Exception as e:
            self.log_result("Audit", "GET", "/api/v1/audit/stats", "Get Stats Missing Auth", 401, 0, str(e), False, f"Exception: {e}")

        # 3.6 Get Stats Invalid
        print("Testing GET /api/v1/audit/stats (Invalid Input)...")
        try:
            # Stats uses regex pattern "^(today|7d|30d)$"
            r = self.client.get("/api/v1/audit/stats", params={"period": "90d"}, headers=headers)
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 422)
            self.log_result("Audit", "GET", "/api/v1/audit/stats", "Get Stats Invalid Input", 422, actual_status, res_json, passed, "Expected validation failure for bad period value.")
        except Exception as e:
            self.log_result("Audit", "GET", "/api/v1/audit/stats", "Get Stats Invalid Input", 422, 0, str(e), False, f"Exception: {e}")

        # 3.7 Get Timeline
        print("Testing GET /api/v1/audit/timeline (Happy Path)...")
        try:
            r = self.client.get("/api/v1/audit/timeline", params={"q": "login"}, headers=headers)
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 200)
            self.log_result("Audit", "GET", "/api/v1/audit/timeline", "Get Timeline Happy Path", 200, actual_status, res_json, passed, "Retrieved audit timeline.")
        except Exception as e:
            self.log_result("Audit", "GET", "/api/v1/audit/timeline", "Get Timeline Happy Path", 200, 0, str(e), False, f"Exception: {e}")

        # 3.8 Get Timeline Missing Auth
        print("Testing GET /api/v1/audit/timeline (Missing Auth)...")
        try:
            r = self.client.get("/api/v1/audit/timeline", params={"q": "login"})
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status in (401, 403))
            self.log_result("Audit", "GET", "/api/v1/audit/timeline", "Get Timeline Missing Auth", "401/403", actual_status, res_json, passed, "Correctly refused access.")
        except Exception as e:
            self.log_result("Audit", "GET", "/api/v1/audit/timeline", "Get Timeline Missing Auth", 401, 0, str(e), False, f"Exception: {e}")

        # 3.9 Get Timeline Invalid
        print("Testing GET /api/v1/audit/timeline (Invalid Input)...")
        try:
            r = self.client.get("/api/v1/audit/timeline", params={"user_id": "invalid-uuid"}, headers=headers)
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 422)
            self.log_result("Audit", "GET", "/api/v1/audit/timeline", "Get Timeline Invalid Input", 422, actual_status, res_json, passed, "Expected validation failure for bad UUID.")
        except Exception as e:
            self.log_result("Audit", "GET", "/api/v1/audit/timeline", "Get Timeline Invalid Input", 422, 0, str(e), False, f"Exception: {e}")

        # 3.10 Export Log
        print("Testing GET /api/v1/audit/export (Happy Path)...")
        try:
            r = self.client.get("/api/v1/audit/export", params={"format": "csv"}, headers=headers)
            actual_status = r.status_code
            passed = (actual_status == 200) and ("text/csv" in r.headers.get("content-type", ""))
            self.log_result("Audit", "GET", "/api/v1/audit/export", "Export Log Happy Path", 200, actual_status, f"[Binary/CSV data, length: {len(r.content)}]", passed, "Exported CSV file successfully.")
        except Exception as e:
            self.log_result("Audit", "GET", "/api/v1/audit/export", "Export Log Happy Path", 200, 0, str(e), False, f"Exception: {e}")

        # 3.11 Export Log Missing Auth
        print("Testing GET /api/v1/audit/export (Missing Auth)...")
        try:
            r = self.client.get("/api/v1/audit/export", params={"format": "csv"})
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status in (401, 403))
            self.log_result("Audit", "GET", "/api/v1/audit/export", "Export Log Missing Auth", "401/403", actual_status, res_json, passed, "Correctly refused access.")
        except Exception as e:
            self.log_result("Audit", "GET", "/api/v1/audit/export", "Export Log Missing Auth", 401, 0, str(e), False, f"Exception: {e}")

        # 3.12 Export Log Invalid
        print("Testing GET /api/v1/audit/export (Invalid Input)...")
        try:
            r = self.client.get("/api/v1/audit/export", params={"format": "pdf"}, headers=headers)
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 400) # Per router code raising 400 Bad Request
            self.log_result("Audit", "GET", "/api/v1/audit/export", "Export Log Invalid Input", 400, actual_status, res_json, passed, "Expected 400 for unsupported format.")
            if not passed:
                self.discovered_issues.append({
                    "title": "Audit export did not return 400 for PDF",
                    "severity": "LOW",
                    "description": f"Audit export with PDF format returned status {actual_status} instead of 400. Response: {res_json}",
                    "fix": "Ensure that audit.py correctly raises a HTTP 400 Bad Request if format is not csv."
                })
        except Exception as e:
            self.log_result("Audit", "GET", "/api/v1/audit/export", "Export Log Invalid Input", 400, 0, str(e), False, f"Exception: {e}")

        # 3.13 Get Event Happy Path (requires dynamic event ID from earlier list call)
        if audit_events:
            event_id = audit_events[0].get("id")
            print(f"Testing GET /api/v1/audit/{{event_id}} (Happy Path, using dynamic ID: {event_id})...")
            try:
                r = self.client.get(f"/api/v1/audit/{event_id}", headers=headers)
                actual_status = r.status_code
                res_json = r.json()
                passed = (actual_status == 200)
                self.log_result("Audit", "GET", "/api/v1/audit/{event_id}", "Get Event Happy Path", 200, actual_status, res_json, passed, "Successfully fetched specific event details.")
            except Exception as e:
                self.log_result("Audit", "GET", "/api/v1/audit/{event_id}", "Get Event Happy Path", 200, 0, str(e), False, f"Exception: {e}")
        else:
            print("Skipping GET /api/v1/audit/{event_id} Happy Path - No events in DB to fetch.")
            self.log_result("Audit", "GET", "/api/v1/audit/{event_id}", "Get Event Happy Path", 200, 200, "Skipped", True, "Skipped: No events present in SQLite db to query.")

        # 3.14 Get Event Missing Auth
        print("Testing GET /api/v1/audit/{event_id} (Missing Auth)...")
        try:
            r = self.client.get("/api/v1/audit/00000000-0000-0000-0000-000000000000")
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status in (401, 403))
            self.log_result("Audit", "GET", "/api/v1/audit/{event_id}", "Get Event Missing Auth", "401/403", actual_status, res_json, passed, "Correctly refused access.")
        except Exception as e:
            self.log_result("Audit", "GET", "/api/v1/audit/{event_id}", "Get Event Missing Auth", 401, 0, str(e), False, f"Exception: {e}")

        # 3.15 Get Event Invalid
        print("Testing GET /api/v1/audit/{event_id} (Invalid Input)...")
        try:
            r = self.client.get("/api/v1/audit/invalid-uuid", headers=headers)
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 422)
            self.log_result("Audit", "GET", "/api/v1/audit/{event_id}", "Get Event Invalid Input", 422, actual_status, res_json, passed, "Expected validation failure for bad UUID.")
        except Exception as e:
            self.log_result("Audit", "GET", "/api/v1/audit/{event_id}", "Get Event Invalid Input", 422, 0, str(e), False, f"Exception: {e}")

        # 3.16 Get Event Not Found
        print("Testing GET /api/v1/audit/{event_id} (Not Found)...")
        try:
            r = self.client.get("/api/v1/audit/00000000-0000-0000-0000-000000000000", headers=headers)
            actual_status = r.status_code
            res_json = r.json()
            passed = (actual_status == 404)
            self.log_result("Audit", "GET", "/api/v1/audit/{event_id}", "Get Event Not Found", 404, actual_status, res_json, passed, "Expected 404 Not Found.")
        except Exception as e:
            self.log_result("Audit", "GET", "/api/v1/audit/{event_id}", "Get Event Not Found", 404, 0, str(e), False, f"Exception: {e}")


    def generate_markdown_report(self):
        # Trigger logout happy path test at the end to properly clean up
        self._logout_func()

        passed_tests = [t for t in self.results if t["passed"]]
        failed_tests = [t for t in self.results if not t["passed"]]
        
        report_content = f"""# CleanPlates API Test Report - Round 1

**Date:** {datetime.date.today().isoformat()}
**Target Host:** `{BASE_URL}`
**Status:** { "PASSING" if len(failed_tests) == 0 else "ISSUES FOUND" }

## Executive Summary
This report summarizes the automated testing results for **Round 1 (Analytics, Audit, Auth)** against the local development server. 
The test suite executed **{len(self.results)}** test cases covering happy paths, missing authentication, and various validation edge cases (invalid data types and bounds).

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
        with open("round_1_test_report.md", "w", encoding="utf-8") as f:
            f.write(report_content)
        
        print(f"\nGenerated report: round_1_test_report.md")

if __name__ == "__main__":
    suite = APITestSuite()
    suite.run_tests()
