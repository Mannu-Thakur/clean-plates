# CleanPlates API Test Report - Round 6

**Date:** 2026-05-17
**Target Host:** `http://127.0.0.1:8000`
**Status:** PASSING

## Executive Summary
This report summarizes the automated testing results for **Round 6 (Students, Warnings, Waste)** against the local development server. 
The test suite executed **95** test cases covering happy paths, missing authentication, and various validation edge cases (missing required fields, invalid types, and value bounds).

* **Total Test Cases Executed:** 95
* **Passed:** 95
* **Failed:** 0

---

## Issues Discovered
No critical architectural or functional issues were discovered. All endpoint behaviors matched expected specifications.

---

## Test Cases Summary
| Category | Method | Endpoint | Test Name | Expected | Actual | Passed | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Students | `GET` | `/api/v1/students/` | List Students (Happy Path) | `200` | `200` | ✅ PASS | Fetched student registry successfully. |
| Students | `GET` | `/api/v1/students/` | List Students (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Students | `GET` | `/api/v1/students/export` | Export Students (Happy Path) | `200` | `200` | ✅ PASS | Exported students CSV successfully. |
| Students | `GET` | `/api/v1/students/export` | Export Students (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Students | `POST` | `/api/v1/students/import-mapping` | Import Mappings (Happy Path) | `200` | `200` | ✅ PASS | Uploaded and mapped students via CSV. |
| Students | `POST` | `/api/v1/students/import-mapping` | Import Mappings (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for empty payload. |
| Students | `POST` | `/api/v1/students/import-mapping` | Import Mappings (Invalid Format) | `400/422` | `400` | ✅ PASS | Expected bad request error for unsupported text extension. |
| Students | `POST` | `/api/v1/students/bulk/warn` | Bulk Warn Students (Happy Path) | `200` | `200` | ✅ PASS | Successfully issued bulk warnings. |
| Students | `POST` | `/api/v1/students/bulk/warn` | Bulk Warn Students (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for missing student_ids and reason. |
| Students | `POST` | `/api/v1/students/bulk/warn` | Bulk Warn Students (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for invalid types. |
| Students | `GET` | `/api/v1/students/{student_id}` | Get Student (Happy Path) | `200` | `200` | ✅ PASS | Fetched student profile successfully. |
| Students | `GET` | `/api/v1/students/{student_id}` | Get Student (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Students | `GET` | `/api/v1/students/{student_id}` | Get Student (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Students | `PATCH` | `/api/v1/students/{student_id}` | Update Profile (Happy Path) | `200` | `200` | ✅ PASS | Updated student active status. |
| Students | `PATCH` | `/api/v1/students/{student_id}` | Update Profile (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Students | `PATCH` | `/api/v1/students/{student_id}` | Update Profile (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for malformed bool. |
| Students | `PATCH` | `/api/v1/students/{student_id}` | Update Profile (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Students | `POST` | `/api/v1/students/{student_id}/map` | Map Card ID (Happy Path) | `200` | `200` | ✅ PASS | Registered student card profile details. |
| Students | `POST` | `/api/v1/students/{student_id}/map` | Map Card ID (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for missing required fields. |
| Students | `POST` | `/api/v1/students/{student_id}/map` | Map Card ID (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for malformed types. |
| Students | `POST` | `/api/v1/students/{student_id}/map` | Map Card ID (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Students | `PATCH` | `/api/v1/students/{student_id}/map` | Update Mapping (Happy Path) | `200` | `200` | ✅ PASS | Updated card mapping details successfully. |
| Students | `PATCH` | `/api/v1/students/{student_id}/map` | Update Mapping (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Students | `PATCH` | `/api/v1/students/{student_id}/map` | Update Mapping (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for malformed year. |
| Students | `PATCH` | `/api/v1/students/{student_id}/map` | Update Mapping (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Students | `GET` | `/api/v1/students/{student_id}/stats` | Get Student Stats (Happy Path) | `200` | `200` | ✅ PASS | Fetched student analytics statistics. |
| Students | `GET` | `/api/v1/students/{student_id}/stats` | Get Student Stats (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Students | `GET` | `/api/v1/students/{student_id}/stats` | Get Student Stats (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Students | `GET` | `/api/v1/students/{student_id}/timeline` | Get Student Timeline (Happy Path) | `200` | `200` | ✅ PASS | Fetched student timeline series. |
| Students | `GET` | `/api/v1/students/{student_id}/timeline` | Get Student Timeline (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Students | `GET` | `/api/v1/students/{student_id}/timeline` | Get Student Timeline (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Students | `GET` | `/api/v1/students/{student_id}/food-breakdown` | Get Food Breakdown (Happy Path) | `200` | `200` | ✅ PASS | Fetched student food item breakdown. |
| Students | `GET` | `/api/v1/students/{student_id}/food-breakdown` | Get Food Breakdown (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Students | `GET` | `/api/v1/students/{student_id}/food-breakdown` | Get Food Breakdown (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Students | `GET` | `/api/v1/students/{student_id}/meal-pattern` | Get Meal Pattern (Happy Path) | `200` | `200` | ✅ PASS | Fetched student meal patterns. |
| Students | `GET` | `/api/v1/students/{student_id}/meal-pattern` | Get Meal Pattern (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Students | `GET` | `/api/v1/students/{student_id}/meal-pattern` | Get Meal Pattern (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Students | `GET` | `/api/v1/students/{student_id}/improvement` | Get Student Improvement (Happy Path) | `200` | `200` | ✅ PASS | Fetched student improvement trends. |
| Students | `GET` | `/api/v1/students/{student_id}/improvement` | Get Student Improvement (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Students | `GET` | `/api/v1/students/{student_id}/improvement` | Get Student Improvement (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Students | `GET` | `/api/v1/students/{student_id}/history` | Get Student History (Happy Path) | `200` | `200` | ✅ PASS | Fetched student historic logs. |
| Students | `GET` | `/api/v1/students/{student_id}/history` | Get Student History (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Students | `GET` | `/api/v1/students/{student_id}/history` | Get Student History (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Students | `GET` | `/api/v1/students/{student_id}/warnings` | Get Student Warnings (Happy Path) | `200` | `200` | ✅ PASS | Fetched student warnings list. |
| Students | `GET` | `/api/v1/students/{student_id}/warnings` | Get Student Warnings (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Students | `GET` | `/api/v1/students/{student_id}/warnings` | Get Student Warnings (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Students | `POST` | `/api/v1/students/{student_id}/warnings` | Create Warning (Happy Path) | `201` | `201` | ✅ PASS | Created individual student warning. |
| Students | `POST` | `/api/v1/students/{student_id}/warnings` | Create Warning (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for missing reason. |
| Students | `POST` | `/api/v1/students/{student_id}/warnings` | Create Warning (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for bad types. |
| Students | `POST` | `/api/v1/students/{student_id}/warnings` | Create Warning (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Students | `POST` | `/api/v1/students/{student_id}/penalties` | Create Penalty Direct (Happy Path) | `201` | `201` | ✅ PASS | Created direct student penalty. |
| Students | `POST` | `/api/v1/students/{student_id}/penalties` | Create Penalty Direct (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for missing reason. |
| Students | `POST` | `/api/v1/students/{student_id}/penalties` | Create Penalty Direct (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for bad types. |
| Students | `POST` | `/api/v1/students/{student_id}/penalties` | Create Penalty Direct (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Warnings | `GET` | `/api/v1/warnings/` | List Warnings (Happy Path) | `200` | `200` | ✅ PASS | Fetched overall warnings list. |
| Warnings | `GET` | `/api/v1/warnings/` | List Warnings (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Warnings | `GET` | `/api/v1/warnings/stats` | Get Warning Stats (Happy Path) | `200` | `200` | ✅ PASS | Fetched system-wide warning/penalty stats. |
| Warnings | `GET` | `/api/v1/warnings/stats` | Get Warning Stats (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Warnings | `GET` | `/api/v1/warnings/export` | Export Warnings (Happy Path) | `200` | `200` | ✅ PASS | Exported warnings to CSV file. |
| Warnings | `GET` | `/api/v1/warnings/export` | Export Warnings (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Warnings | `PATCH` | `/api/v1/warnings/bulk/resolve` | Bulk Resolve Warnings (Happy Path) | `200` | `200` | ✅ PASS | Successfully resolved warning IDs. |
| Warnings | `PATCH` | `/api/v1/warnings/bulk/resolve` | Bulk Resolve Warnings (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for empty payload. |
| Warnings | `PATCH` | `/api/v1/warnings/bulk/resolve` | Bulk Resolve Warnings (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for malformed types. |
| Warnings | `PATCH` | `/api/v1/warnings/{warning_id}/resolve` | Resolve Warning (Happy Path) | `200` | `200` | ✅ PASS | Resolved warning successfully. |
| Warnings | `PATCH` | `/api/v1/warnings/{warning_id}/resolve` | Resolve Warning (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for empty body. |
| Warnings | `PATCH` | `/api/v1/warnings/{warning_id}/resolve` | Resolve Warning (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for bad note type. |
| Warnings | `PATCH` | `/api/v1/warnings/{warning_id}/resolve` | Resolve Warning (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Warnings | `POST` | `/api/v1/warnings/{warning_id}/escalate` | Escalate Warning (Happy Path) | `200/201` | `200` | ✅ PASS | Escalated warning successfully. |
| Warnings | `POST` | `/api/v1/warnings/{warning_id}/escalate` | Escalate Warning (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for empty body. |
| Warnings | `POST` | `/api/v1/warnings/{warning_id}/escalate` | Escalate Warning (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for bad types. |
| Warnings | `POST` | `/api/v1/warnings/{warning_id}/escalate` | Escalate Warning (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Warnings | `POST` | `/api/v1/warnings/{warning_id}/apply-penalty` | Apply Penalty to Warning (Happy Path) | `200/201` | `200` | ✅ PASS | Converted warning to penalty successfully. |
| Warnings | `POST` | `/api/v1/warnings/{warning_id}/apply-penalty` | Apply Penalty to Warning (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Warnings | `POST` | `/api/v1/warnings/{warning_id}/apply-penalty` | Apply Penalty to Warning (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Warnings | `GET` | `/api/v1/penalties/` | List Penalties (Happy Path) | `200` | `200` | ✅ PASS | Fetched student penalties list. |
| Warnings | `GET` | `/api/v1/penalties/` | List Penalties (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Warnings | `PATCH` | `/api/v1/penalties/{penalty_id}/revoke` | Revoke Penalty (Happy Path) | `200` | `200` | ✅ PASS | Revoked penalty successfully. |
| Warnings | `PATCH` | `/api/v1/penalties/{penalty_id}/revoke` | Revoke Penalty (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for empty body. |
| Warnings | `PATCH` | `/api/v1/penalties/{penalty_id}/revoke` | Revoke Penalty (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for bad reason type. |
| Warnings | `PATCH` | `/api/v1/penalties/{penalty_id}/revoke` | Revoke Penalty (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Warnings | `GET` | `/api/v1/escalations/` | List Escalations (Happy Path) | `200` | `200` | ✅ PASS | Fetched warning escalations registry. |
| Warnings | `GET` | `/api/v1/escalations/` | List Escalations (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Warnings | `POST` | `/api/v1/escalations/{escalation_id}/review` | Review Escalation (Happy Path) | `200` | `200` | ✅ PASS | Reviewed and processed escalation. |
| Warnings | `POST` | `/api/v1/escalations/{escalation_id}/review` | Review Escalation (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for missing decision. |
| Warnings | `POST` | `/api/v1/escalations/{escalation_id}/review` | Review Escalation (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for invalid decision type. |
| Warnings | `POST` | `/api/v1/escalations/{escalation_id}/review` | Review Escalation (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Waste | `GET` | `/api/v1/waste/entries` | List Entries (Happy Path) | `200` | `200` | ✅ PASS | Fetched waste entries registry successfully. |
| Waste | `GET` | `/api/v1/waste/entries` | List Entries (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Waste | `GET` | `/api/v1/waste/entries/{entry_id}` | Get Entry (Happy Path) | `200` | `200` | ✅ PASS | Fetched single waste entry successfully. |
| Waste | `GET` | `/api/v1/waste/entries/{entry_id}` | Get Entry (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Waste | `GET` | `/api/v1/waste/entries/{entry_id}` | Get Entry (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Waste | `GET` | `/api/v1/waste/current-session` | Get Current Session (Happy Path) | `200` | `200` | ✅ PASS | Fetched device current active session details. |
| Waste | `GET` | `/api/v1/waste/current-session` | Get Current Session (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Waste | `GET` | `/api/v1/waste/recent` | Get Recent Entries (Happy Path) | `200` | `200` | ✅ PASS | Fetched recent waste entries. |
| Waste | `GET` | `/api/v1/waste/recent` | Get Recent Entries (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |

---

## Detailed Failed Test Cases Logs
All executed test cases passed successfully. No failures to log.
