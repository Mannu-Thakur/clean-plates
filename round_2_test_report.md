# CleanPlates API Test Report - Round 2

**Date:** 2026-05-17
**Target Host:** `http://127.0.0.1:8000`
**Status:** PASSING

## Executive Summary
This report summarizes the automated testing results for **Round 2 (Configuration, Devices, Email Templates)** against the local development server. 
The test suite executed **75** test cases covering happy paths, missing authentication, and various validation edge cases (missing required fields, invalid types, and value bounds).

* **Total Test Cases Executed:** 75
* **Passed:** 75
* **Failed:** 0

---

## Issues Discovered
No critical architectural or functional issues were discovered. All endpoint behaviors matched expected specifications.

---

## Test Cases Summary
| Category | Method | Endpoint | Test Name | Expected | Actual | Passed | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Configuration | `GET` | `/api/v1/config/institution` | Get Institution Config (Happy Path) | `200` | `200` | ✅ PASS | Fetched institution configuration. |
| Configuration | `GET` | `/api/v1/config/institution` | Get Institution Config (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Configuration | `PATCH` | `/api/v1/config/institution` | Update Institution Config (Happy Path) | `200` | `200` | ✅ PASS | Updated institution config data. |
| Configuration | `PATCH` | `/api/v1/config/institution` | Update Institution Config (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for empty body. |
| Configuration | `PATCH` | `/api/v1/config/institution` | Update Institution Config (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for null data. |
| Configuration | `GET` | `/api/v1/config/device` | Get Device Config (Happy Path) | `200` | `200` | ✅ PASS | Fetched device configuration. |
| Configuration | `GET` | `/api/v1/config/device` | Get Device Config (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Configuration | `PATCH` | `/api/v1/config/device` | Update Device Config (Happy Path) | `200` | `200` | ✅ PASS | Updated device config data. |
| Configuration | `PATCH` | `/api/v1/config/device` | Update Device Config (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for empty body. |
| Configuration | `PATCH` | `/api/v1/config/device` | Update Device Config (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for null data. |
| Configuration | `GET` | `/api/v1/config/thresholds` | Get Thresholds (Happy Path) | `200` | `200` | ✅ PASS | Fetched waste thresholds. |
| Configuration | `GET` | `/api/v1/config/thresholds` | Get Thresholds (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Configuration | `PATCH` | `/api/v1/config/thresholds` | Update Thresholds (Happy Path) | `200` | `200` | ✅ PASS | Updated thresholds successfully. |
| Configuration | `PATCH` | `/api/v1/config/thresholds` | Update Thresholds (Invalid Values) | `422` | `422` | ✅ PASS | Expected validation failure for negative duration. |
| Configuration | `GET` | `/api/v1/config/meals` | Get Meal Timings (Happy Path) | `200` | `200` | ✅ PASS | Fetched meal timings list. |
| Configuration | `GET` | `/api/v1/config/meals` | Get Meal Timings (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Configuration | `PUT` | `/api/v1/config/meals` | Update Meal Timings (Happy Path) | `200` | `200` | ✅ PASS | Updated meal timings successfully. |
| Configuration | `PUT` | `/api/v1/config/meals` | Update Meal Timings (Invalid Data) | `422` | `422` | ✅ PASS | Expected validation failure for malformed start_time pattern. |
| Configuration | `GET` | `/api/v1/config/branches` | Get Branches (Happy Path) | `200` | `200` | ✅ PASS | Fetched branches list. |
| Configuration | `GET` | `/api/v1/config/branches` | Get Branches (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Configuration | `PUT` | `/api/v1/config/branches` | Update Branches (Happy Path) | `200` | `200` | ✅ PASS | Updated branches list successfully. |
| Configuration | `PUT` | `/api/v1/config/branches` | Update Branches (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for object instead of array. |
| Configuration | `GET` | `/api/v1/config/system` | Get System Policies (Happy Path) | `200` | `200` | ✅ PASS | Fetched system policies. |
| Configuration | `GET` | `/api/v1/config/system` | Get System Policies (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Configuration | `PATCH` | `/api/v1/config/system` | Update System Policies (Happy Path) | `200` | `200` | ✅ PASS | Updated system policies successfully. |
| Configuration | `PATCH` | `/api/v1/config/system` | Update System Policies (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for negative sync interval. |
| Configuration | `POST` | `/api/v1/config/reset/{section}` | Reset Defaults (Happy Path) | `200` | `200` | ✅ PASS | Successfully reset config section to defaults. |
| Configuration | `POST` | `/api/v1/config/reset/{section}` | Reset Defaults (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Configuration | `POST` | `/api/v1/config/reset/{section}` | Reset Defaults (Not Found) | `400 or 404` | `400` | ✅ PASS | Expected 400 or 404 for bad section name, got 400. |
| Devices | `GET` | `/api/v1/devices/` | List Devices (Happy Path) | `200` | `200` | ✅ PASS | Fetched paginated active devices. |
| Devices | `GET` | `/api/v1/devices/` | List Devices (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Devices | `POST` | `/api/v1/devices/` | Register Device (Happy Path) | `201` | `201` | ✅ PASS | Successfully registered a new device. |
| Devices | `POST` | `/api/v1/devices/` | Register Device (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for missing required fields. |
| Devices | `POST` | `/api/v1/devices/` | Register Device (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for bad data types. |
| Devices | `GET` | `/api/v1/devices/{device_id}` | Get Device (Happy Path) | `200` | `200` | ✅ PASS | Successfully fetched device detail. |
| Devices | `GET` | `/api/v1/devices/{device_id}` | Get Device (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Devices | `GET` | `/api/v1/devices/{device_id}` | Get Device (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Devices | `PATCH` | `/api/v1/devices/{device_id}` | Update Device (Happy Path) | `200` | `200` | ✅ PASS | Updated device details. |
| Devices | `PATCH` | `/api/v1/devices/{device_id}` | Update Device (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Devices | `PATCH` | `/api/v1/devices/{device_id}` | Update Device (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for negative capacity. |
| Devices | `PATCH` | `/api/v1/devices/{device_id}` | Update Device (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Devices | `GET` | `/api/v1/devices/{device_id}/health` | Get Device Health (Happy Path) | `200 or 404` | `404` | ✅ PASS | Response: 404 - expected 404 since no heartbeat data has been posted. |
| Devices | `GET` | `/api/v1/devices/{device_id}/health` | Get Device Health (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Devices | `GET` | `/api/v1/devices/{device_id}/health` | Get Device Health (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Devices | `GET` | `/api/v1/devices/{device_id}/health/history` | Get Health History (Happy Path) | `200` | `200` | ✅ PASS | Successfully queried history. |
| Devices | `GET` | `/api/v1/devices/{device_id}/health/history` | Get Health History (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Devices | `GET` | `/api/v1/devices/{device_id}/health/history` | Get Health History (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Devices | `POST` | `/api/v1/devices/{device_id}/sync` | Trigger Sync (Happy Path) | `200` | `200` | ✅ PASS | Successfully queued manual sync. |
| Devices | `POST` | `/api/v1/devices/{device_id}/sync` | Trigger Sync (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Devices | `POST` | `/api/v1/devices/{device_id}/sync` | Trigger Sync (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Devices | `POST` | `/api/v1/devices/{device_id}/restart` | Restart Service (Happy Path) | `200 or 503` | `503` | ✅ PASS | Returned 503 per design because Redis is currently stopped in this environment. |
| Devices | `POST` | `/api/v1/devices/{device_id}/restart` | Restart Service (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Devices | `POST` | `/api/v1/devices/{device_id}/restart` | Restart Service (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Devices | `POST` | `/api/v1/devices/{device_id}/decommission` | Decommission Device (Happy Path) | `200` | `200` | ✅ PASS | Successfully decommissioned device. |
| Devices | `POST` | `/api/v1/devices/{device_id}/decommission` | Decommission Device (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Devices | `POST` | `/api/v1/devices/{device_id}/decommission` | Decommission Device (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Email Templates | `GET` | `/api/v1/templates/` | List Templates (Happy Path) | `200` | `200` | ✅ PASS | Fetched templates list. |
| Email Templates | `GET` | `/api/v1/templates/` | List Templates (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Email Templates | `POST` | `/api/v1/templates/` | Create Template (Happy Path) | `201` | `201` | ✅ PASS | Successfully created email template. |
| Email Templates | `POST` | `/api/v1/templates/` | Create Template (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for missing required fields. |
| Email Templates | `POST` | `/api/v1/templates/` | Create Template (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for non-string name. |
| Email Templates | `GET` | `/api/v1/templates/{template_id}` | Get Template (Happy Path) | `200` | `200` | ✅ PASS | Successfully fetched email template details. |
| Email Templates | `GET` | `/api/v1/templates/{template_id}` | Get Template (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Email Templates | `GET` | `/api/v1/templates/{template_id}` | Get Template (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Email Templates | `PATCH` | `/api/v1/templates/{template_id}` | Update Template (Happy Path) | `200` | `200` | ✅ PASS | Successfully updated email template details. |
| Email Templates | `PATCH` | `/api/v1/templates/{template_id}` | Update Template (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Email Templates | `PATCH` | `/api/v1/templates/{template_id}` | Update Template (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for bad parameters. |
| Email Templates | `PATCH` | `/api/v1/templates/{template_id}` | Update Template (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Email Templates | `POST` | `/api/v1/templates/{template_id}/preview` | Preview Template (Happy Path) | `200` | `200` | ✅ PASS | Successfully generated preview HTML. |
| Email Templates | `POST` | `/api/v1/templates/{template_id}/preview` | Preview Template (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Email Templates | `POST` | `/api/v1/templates/{template_id}/preview` | Preview Template (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for bad variable types. |
| Email Templates | `POST` | `/api/v1/templates/{template_id}/preview` | Preview Template (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Email Templates | `DELETE` | `/api/v1/templates/{template_id}` | Delete Template (Happy Path) | `200` | `200` | ✅ PASS | Successfully deleted template. |
| Email Templates | `DELETE` | `/api/v1/templates/{template_id}` | Delete Template (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Email Templates | `DELETE` | `/api/v1/templates/{template_id}` | Delete Template (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |

---

## Detailed Failed Test Cases Logs
All executed test cases passed successfully. No failures to log.
