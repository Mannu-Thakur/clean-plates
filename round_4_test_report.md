# CleanPlates API Test Report - Round 4

**Date:** 2026-05-17
**Target Host:** `http://127.0.0.1:8000`
**Status:** PASSING

## Executive Summary
This report summarizes the automated testing results for **Round 4 (Monitoring, Notifications, Reports)** against the local development server. 
The test suite executed **65** test cases covering happy paths, missing authentication, and various validation edge cases (missing required fields, invalid types, and value bounds).

* **Total Test Cases Executed:** 65
* **Passed:** 65
* **Failed:** 0

---

## Issues Discovered
No critical architectural or functional issues were discovered. All endpoint behaviors matched expected specifications.

---

## Test Cases Summary
| Category | Method | Endpoint | Test Name | Expected | Actual | Passed | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Monitoring | `GET` | `/api/v1/monitoring/current-session` | Current Session (Happy Path) | `200` | `200` | ✅ PASS | Fetched current session details successfully. |
| Monitoring | `GET` | `/api/v1/monitoring/current-session` | Current Session (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Monitoring | `GET` | `/api/v1/monitoring/current-session` | Current Session (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for invalid UUID. |
| Monitoring | `GET` | `/api/v1/monitoring/recent-entries` | Recent Entries (Happy Path) | `200` | `200` | ✅ PASS | Fetched recent entries list. |
| Monitoring | `GET` | `/api/v1/monitoring/recent-entries` | Recent Entries (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Monitoring | `GET` | `/api/v1/monitoring/recent-entries` | Recent Entries (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for invalid UUID. |
| Monitoring | `GET` | `/api/v1/monitoring/recent-entries` | Recent Entries (Out of Bounds) | `422` | `422` | ✅ PASS | Expected validation failure for limit > 100. |
| Monitoring | `GET` | `/api/v1/monitoring/device-statuses` | Device Statuses (Happy Path) | `200` | `200` | ✅ PASS | Fetched all connected devices and statuses. |
| Monitoring | `GET` | `/api/v1/monitoring/device-statuses` | Device Statuses (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Monitoring | `POST` | `/api/v1/monitoring/alerts/{notif_id}/acknowledge` | Acknowledge Alert (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Monitoring | `POST` | `/api/v1/monitoring/alerts/{notif_id}/acknowledge` | Acknowledge Alert (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for non-UUID identifier. |
| Monitoring | `POST` | `/api/v1/monitoring/alerts/{notif_id}/acknowledge` | Acknowledge Alert (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Notifications | `GET` | `/api/v1/notifications/` | List Notifications (Happy Path) | `200` | `200` | ✅ PASS | Fetched notification log successfully. |
| Notifications | `GET` | `/api/v1/notifications/` | List Notifications (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Notifications | `POST` | `/api/v1/notifications/` | Send Notification (Happy Path) | `201` | `201` | ✅ PASS | Created and queued new notification. |
| Notifications | `POST` | `/api/v1/notifications/` | Send Notification (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for missing fields. |
| Notifications | `POST` | `/api/v1/notifications/` | Send Notification (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for invalid channel. |
| Notifications | `GET` | `/api/v1/notifications/stats` | Get Notification Stats (Happy Path) | `200` | `200` | ✅ PASS | Fetched notification engine operational status. |
| Notifications | `GET` | `/api/v1/notifications/stats` | Get Notification Stats (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Notifications | `POST` | `/api/v1/notifications/broadcast` | Send Broadcast (Happy Path) | `200` | `200` | ✅ PASS | Sent system broadcast successfully. |
| Notifications | `POST` | `/api/v1/notifications/broadcast` | Send Broadcast (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for missing required fields. |
| Notifications | `POST` | `/api/v1/notifications/broadcast` | Send Broadcast (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for non-string channel type. |
| Notifications | `POST` | `/api/v1/notifications/schedule` | Schedule Notification (Happy Path) | `201` | `201` | ✅ PASS | Scheduled future notification successfully. |
| Notifications | `POST` | `/api/v1/notifications/schedule` | Schedule Notification (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for missing scheduled date. |
| Notifications | `POST` | `/api/v1/notifications/schedule` | Schedule Notification (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for bad ISO datetime format. |
| Notifications | `POST` | `/api/v1/notifications/mark-all-read` | Mark All Read (Happy Path) | `200` | `200` | ✅ PASS | Marked inbox notifications as read. |
| Notifications | `POST` | `/api/v1/notifications/mark-all-read` | Mark All Read (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Notifications | `GET` | `/api/v1/notifications/{notif_id}/delivery` | Get Delivery Status (Happy Path) | `200` | `200` | ✅ PASS | Obtained delivery stats for the created notification. |
| Notifications | `GET` | `/api/v1/notifications/{notif_id}/delivery` | Get Delivery Status (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Notifications | `GET` | `/api/v1/notifications/{notif_id}/delivery` | Get Delivery Status (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Notifications | `GET` | `/api/v1/notifications/{notif_id}` | Get Notification (Happy Path) | `200` | `200` | ✅ PASS | Fetched notification detail payload. |
| Notifications | `GET` | `/api/v1/notifications/{notif_id}` | Get Notification (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Notifications | `GET` | `/api/v1/notifications/{notif_id}` | Get Notification (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Notifications | `PATCH` | `/api/v1/notifications/{notif_id}/read` | Mark Read (Happy Path) | `200` | `200` | ✅ PASS | Marked notification as read successfully. |
| Notifications | `PATCH` | `/api/v1/notifications/{notif_id}/read` | Mark Read (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Notifications | `PATCH` | `/api/v1/notifications/{notif_id}/read` | Mark Read (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Notifications | `POST` | `/api/v1/notifications/{notif_id}/retry` | Retry Failed (Happy Path) | `200/409` | `409` | ✅ PASS | Triggered retry or correctly received 409 for non-failed notification. |
| Notifications | `POST` | `/api/v1/notifications/{notif_id}/retry` | Retry Failed (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Notifications | `POST` | `/api/v1/notifications/{notif_id}/retry` | Retry Failed (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Notifications | `DELETE` | `/api/v1/notifications/{notif_id}` | Delete Notification (Happy Path) | `200` | `200` | ✅ PASS | Deleted target notification archive. |
| Notifications | `DELETE` | `/api/v1/notifications/{notif_id}` | Delete Notification (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Notifications | `DELETE` | `/api/v1/notifications/{notif_id}` | Delete Notification (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Reports | `GET` | `/api/v1/reports/` | List Reports (Happy Path) | `200` | `200` | ✅ PASS | Fetched completed reports archive list. |
| Reports | `GET` | `/api/v1/reports/` | List Reports (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Reports | `POST` | `/api/v1/reports/generate` | Generate Report (Happy Path) | `200/201` | `201` | ✅ PASS | Triggered synchronous report compilation. |
| Reports | `POST` | `/api/v1/reports/generate` | Generate Report (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for missing report type. |
| Reports | `POST` | `/api/v1/reports/generate` | Generate Report (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for unsupported extension format. |
| Reports | `GET` | `/api/v1/reports/schedules` | List Schedules (Happy Path) | `200` | `200` | ✅ PASS | Fetched saved report schedules successfully. |
| Reports | `GET` | `/api/v1/reports/schedules` | List Schedules (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Reports | `POST` | `/api/v1/reports/schedules` | Create Schedule (Happy Path) | `201` | `201` | ✅ PASS | Created new report subscription schedule. |
| Reports | `POST` | `/api/v1/reports/schedules` | Create Schedule (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for missing fields. |
| Reports | `POST` | `/api/v1/reports/schedules` | Create Schedule (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for out-of-format time. |
| Reports | `PATCH` | `/api/v1/reports/schedules/{schedule_id}` | Update Schedule (Happy Path) | `200` | `200` | ✅ PASS | Updated schedule configuration parameters. |
| Reports | `PATCH` | `/api/v1/reports/schedules/{schedule_id}` | Update Schedule (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Reports | `PATCH` | `/api/v1/reports/schedules/{schedule_id}` | Update Schedule (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for invalid type. |
| Reports | `PATCH` | `/api/v1/reports/schedules/{schedule_id}` | Update Schedule (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Reports | `DELETE` | `/api/v1/reports/schedules/{schedule_id}` | Delete Schedule (Happy Path) | `200` | `200` | ✅ PASS | Successfully deleted report schedule. |
| Reports | `DELETE` | `/api/v1/reports/schedules/{schedule_id}` | Delete Schedule (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Reports | `DELETE` | `/api/v1/reports/schedules/{schedule_id}` | Delete Schedule (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Reports | `GET` | `/api/v1/reports/{report_id}/download` | Download Report (Happy Path) | `200` | `200` | ✅ PASS | Successfully downloaded generated report payload. |
| Reports | `GET` | `/api/v1/reports/{report_id}/download` | Download Report (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Reports | `GET` | `/api/v1/reports/{report_id}/download` | Download Report (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Reports | `DELETE` | `/api/v1/reports/{report_id}` | Delete Report (Happy Path) | `200` | `200` | ✅ PASS | Successfully deleted report archive entry. |
| Reports | `DELETE` | `/api/v1/reports/{report_id}` | Delete Report (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Reports | `DELETE` | `/api/v1/reports/{report_id}` | Delete Report (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |

---

## Detailed Failed Test Cases Logs
All executed test cases passed successfully. No failures to log.
