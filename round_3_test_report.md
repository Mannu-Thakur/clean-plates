# CleanPlates API Test Report - Round 3

**Date:** 2026-05-17
**Target Host:** `http://127.0.0.1:8000`
**Status:** PASSING

## Executive Summary
This report summarizes the automated testing results for **Round 3 (Filter Presets, Health, ML Ingestion)** against the local development server. 
The test suite executed **33** test cases covering happy paths, missing authentication, and various validation edge cases (missing required fields, invalid types, and value bounds).

* **Total Test Cases Executed:** 33
* **Passed:** 33
* **Failed:** 0

---

## Issues Discovered
No critical architectural or functional issues were discovered. All endpoint behaviors matched expected specifications.

---

## Test Cases Summary
| Category | Method | Endpoint | Test Name | Expected | Actual | Passed | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Filter Presets | `GET` | `/api/v1/filters/presets` | List Presets (Happy Path) | `200` | `200` | ✅ PASS | Fetched saved filter presets successfully. |
| Filter Presets | `GET` | `/api/v1/filters/presets` | List Presets (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Filter Presets | `POST` | `/api/v1/filters/presets` | Save Preset (Happy Path) | `201` | `201` | ✅ PASS | Saved new filter preset view. |
| Filter Presets | `POST` | `/api/v1/filters/presets` | Save Preset (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for missing preset name. |
| Filter Presets | `POST` | `/api/v1/filters/presets` | Save Preset (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for non-string name. |
| Filter Presets | `GET` | `/api/v1/filters/presets/{preset_id}` | Get Preset (Happy Path) | `200` | `200` | ✅ PASS | Successfully fetched saved preset details. |
| Filter Presets | `GET` | `/api/v1/filters/presets/{preset_id}` | Get Preset (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Filter Presets | `GET` | `/api/v1/filters/presets/{preset_id}` | Get Preset (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Filter Presets | `PATCH` | `/api/v1/filters/presets/{preset_id}` | Update Preset (Happy Path) | `200` | `200` | ✅ PASS | Successfully updated preset view attributes. |
| Filter Presets | `PATCH` | `/api/v1/filters/presets/{preset_id}` | Update Preset (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Filter Presets | `PATCH` | `/api/v1/filters/presets/{preset_id}` | Update Preset (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for non-string name. |
| Filter Presets | `PATCH` | `/api/v1/filters/presets/{preset_id}` | Update Preset (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Filter Presets | `DELETE` | `/api/v1/filters/presets/{preset_id}` | Delete Preset (Happy Path) | `200` | `200` | ✅ PASS | Successfully deleted preset. |
| Filter Presets | `DELETE` | `/api/v1/filters/presets/{preset_id}` | Delete Preset (Missing Auth) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Filter Presets | `DELETE` | `/api/v1/filters/presets/{preset_id}` | Delete Preset (Not Found) | `404` | `404` | ✅ PASS | Expected 404 for random UUID. |
| Health | `GET` | `/health` | Health Check (Happy Path) | `200` | `200` | ✅ PASS | Uptime and status check. |
| Health | `GET` | `/health` | Health Check (Missing Auth) | `200 (Public endpoint)` | `200` | ✅ PASS | The health endpoint is intentionally public (as designed in Phase 1) and does not require auth, returning 200. |
| ML Ingestion | `POST` | `/api/v1/ml/detect` | Ingest Detection (Happy Path) | `201` | `201` | ✅ PASS | Successfully recorded waste detection event. |
| ML Ingestion | `POST` | `/api/v1/ml/detect` | Ingest Detection (Missing Auth) | `401` | `401` | ✅ PASS | Correctly refused access without API key. |
| ML Ingestion | `POST` | `/api/v1/ml/detect` | Ingest Detection (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for missing required fields. |
| ML Ingestion | `POST` | `/api/v1/ml/detect` | Ingest Detection (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for invalid parameter types. |
| ML Ingestion | `POST` | `/api/v1/ml/sync` | Bulk Ingest (Happy Path) | `200` | `200` | ✅ PASS | Successfully synchronised offline-queued ML detection data. |
| ML Ingestion | `POST` | `/api/v1/ml/sync` | Bulk Ingest (Missing Auth) | `401` | `401` | ✅ PASS | Correctly refused access without API key. |
| ML Ingestion | `POST` | `/api/v1/ml/sync` | Bulk Ingest (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for empty payload. |
| ML Ingestion | `POST` | `/api/v1/ml/sync` | Bulk Ingest (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for bad parameter types. |
| ML Ingestion | `POST` | `/api/v1/ml/heartbeat` | Ml Heartbeat (Happy Path) | `200` | `200` | ✅ PASS | Successfully logged device CPU/RAM and stats. |
| ML Ingestion | `POST` | `/api/v1/ml/heartbeat` | Ml Heartbeat (Missing Auth) | `401` | `401` | ✅ PASS | Correctly refused access without API key. |
| ML Ingestion | `POST` | `/api/v1/ml/heartbeat` | Ml Heartbeat (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for missing required fields. |
| ML Ingestion | `POST` | `/api/v1/ml/heartbeat` | Ml Heartbeat (Invalid Types) | `422` | `422` | ✅ PASS | Expected validation failure for out-of-bounds parameters. |
| ML Ingestion | `POST` | `/api/v1/ml/upload-image` | Upload Image (Happy Path) | `200` | `200` | ✅ PASS | Successfully uploaded a JPEG test plate image. |
| ML Ingestion | `POST` | `/api/v1/ml/upload-image` | Upload Image (Missing Auth) | `401` | `401` | ✅ PASS | Correctly refused access without API key. |
| ML Ingestion | `POST` | `/api/v1/ml/upload-image` | Upload Image (Missing Required) | `422` | `422` | ✅ PASS | Expected validation failure for missing required file parameter. |
| ML Ingestion | `POST` | `/api/v1/ml/upload-image` | Upload Image (Invalid Format) | `400` | `400` | ✅ PASS | Expected 400 Bad Request for unsupported text file type. |

---

## Detailed Failed Test Cases Logs
All executed test cases passed successfully. No failures to log.
