# CleanPlates API Test Report - Round 1

**Date:** 2026-05-17
**Target Host:** `http://127.0.0.1:8000`
**Status:** PASSING

## Executive Summary
This report summarizes the automated testing results for **Round 1 (Analytics, Audit, Auth)** against the local development server. 
The test suite executed **58** test cases covering happy paths, missing authentication, and various validation edge cases (invalid data types and bounds).

* **Total Test Cases Executed:** 58
* **Passed:** 58
* **Failed:** 0

---

## Issues Discovered
No critical architectural or functional issues were discovered. All endpoint behaviors matched expected specifications.

---

## Test Cases Summary
| Category | Method | Endpoint | Test Name | Expected | Actual | Passed | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Auth | `POST` | `/api/v1/auth/login` | Valid Login (Happy Path) | `200` | `200` | ✅ PASS | Obtained JWT access & refresh tokens. |
| Auth | `POST` | `/api/v1/auth/login` | Missing Required Parameters | `422` | `422` | ✅ PASS | Expected validation failure for missing fields. |
| Auth | `POST` | `/api/v1/auth/login` | Invalid Data Types | `422` | `422` | ✅ PASS | Expected validation failure for bad parameter types. |
| Auth | `POST` | `/api/v1/auth/login` | Bad Credentials | `400 or 401` | `400` | ✅ PASS | Expected 400/401, got 400. |
| Auth | `GET` | `/api/v1/auth/me` | Missing Auth Header | `401/403` | `401` | ✅ PASS | Expected 401/403 for unauthenticated request. |
| Auth | `GET` | `/api/v1/auth/me` | Valid Auth (Happy Path) | `200` | `200` | ✅ PASS | Fetched active user profile. |
| Auth | `POST` | `/api/v1/auth/forgot-password` | Forgot Password Happy Path | `200` | `200` | ✅ PASS | Expected 200 OK. |
| Auth | `POST` | `/api/v1/auth/forgot-password` | Forgot Password Missing Required | `422` | `422` | ✅ PASS | Expected 422 validation failure. |
| Auth | `POST` | `/api/v1/auth/forgot-password` | Forgot Password Invalid Types | `422` | `422` | ✅ PASS | Expected 422 validation failure. |
| Auth | `POST` | `/api/v1/auth/reset-password` | Reset Password with Invalid Token | `400` | `400` | ✅ PASS | Expected 400 Bad Request for bad token. Got 400. |
| Auth | `POST` | `/api/v1/auth/reset-password` | Reset Password Missing Required | `422` | `422` | ✅ PASS | Expected 422 validation failure. |
| Auth | `POST` | `/api/v1/auth/reset-password` | Reset Password Invalid Types | `422` | `422` | ✅ PASS | Expected 422 validation failure. |
| Auth | `POST` | `/api/v1/auth/refresh` | Refresh Tokens Happy Path | `200` | `200` | ✅ PASS | Refreshed access token successfully. |
| Auth | `POST` | `/api/v1/auth/refresh` | Refresh Tokens Missing Required | `422` | `422` | ✅ PASS | Expected 422 validation failure. |
| Auth | `POST` | `/api/v1/auth/refresh` | Refresh Tokens Invalid Types | `422` | `422` | ✅ PASS | Expected 422 validation failure. |
| Auth | `POST` | `/api/v1/auth/logout` | Logout Missing Required | `422` | `422` | ✅ PASS | Expected 422 validation failure. |
| Auth | `POST` | `/api/v1/auth/logout` | Logout Invalid Types | `422` | `422` | ✅ PASS | Expected 422 validation failure. |
| Analytics | `GET` | `/api/v1/analytics/overview` | Happy Path (overview) | `200` | `200` | ✅ PASS | Fetched analytics report successfully. |
| Analytics | `GET` | `/api/v1/analytics/overview` | Missing Auth (overview) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Analytics | `GET` | `/api/v1/analytics/overview` | Invalid Param (overview) | `422` | `422` | ✅ PASS | FastAPI validation rules correctly rejected input. |
| Analytics | `GET` | `/api/v1/analytics/trends` | Happy Path (trends) | `200` | `200` | ✅ PASS | Fetched analytics report successfully. |
| Analytics | `GET` | `/api/v1/analytics/trends` | Missing Auth (trends) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Analytics | `GET` | `/api/v1/analytics/trends` | Invalid Param (trends) | `422` | `422` | ✅ PASS | FastAPI validation rules correctly rejected input. |
| Analytics | `GET` | `/api/v1/analytics/peaks` | Happy Path (peaks) | `200` | `200` | ✅ PASS | Fetched analytics report successfully. |
| Analytics | `GET` | `/api/v1/analytics/peaks` | Missing Auth (peaks) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Analytics | `GET` | `/api/v1/analytics/peaks` | Invalid Param (peaks) | `422` | `422` | ✅ PASS | FastAPI validation rules correctly rejected input. |
| Analytics | `GET` | `/api/v1/analytics/meal-distribution` | Happy Path (meal-distribution) | `200` | `200` | ✅ PASS | Fetched analytics report successfully. |
| Analytics | `GET` | `/api/v1/analytics/meal-distribution` | Missing Auth (meal-distribution) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Analytics | `GET` | `/api/v1/analytics/meal-distribution` | Invalid Param (meal-distribution) | `422` | `422` | ✅ PASS | FastAPI validation rules correctly rejected input. |
| Analytics | `GET` | `/api/v1/analytics/food-waste-distribution` | Happy Path (food-waste-distribution) | `200` | `200` | ✅ PASS | Fetched analytics report successfully. |
| Analytics | `GET` | `/api/v1/analytics/food-waste-distribution` | Missing Auth (food-waste-distribution) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Analytics | `GET` | `/api/v1/analytics/food-waste-distribution` | Invalid Param (food-waste-distribution) | `422` | `422` | ✅ PASS | FastAPI validation rules correctly rejected input. |
| Analytics | `GET` | `/api/v1/analytics/top-waste-contributors` | Happy Path (top-waste-contributors) | `200` | `200` | ✅ PASS | Fetched analytics report successfully. |
| Analytics | `GET` | `/api/v1/analytics/top-waste-contributors` | Missing Auth (top-waste-contributors) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Analytics | `GET` | `/api/v1/analytics/top-waste-contributors` | Invalid Param (top-waste-contributors) | `422` | `422` | ✅ PASS | FastAPI validation rules correctly rejected input. |
| Analytics | `GET` | `/api/v1/analytics/improvement-tracking` | Happy Path (improvement-tracking) | `200` | `200` | ✅ PASS | Fetched analytics report successfully. |
| Analytics | `GET` | `/api/v1/analytics/improvement-tracking` | Missing Auth (improvement-tracking) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Analytics | `GET` | `/api/v1/analytics/improvement-tracking` | Invalid Param (improvement-tracking) | `422` | `422` | ✅ PASS | FastAPI validation rules correctly rejected input. |
| Analytics | `GET` | `/api/v1/analytics/sustainability` | Happy Path (sustainability) | `200` | `200` | ✅ PASS | Fetched analytics report successfully. |
| Analytics | `GET` | `/api/v1/analytics/sustainability` | Missing Auth (sustainability) | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Analytics | `GET` | `/api/v1/analytics/sustainability` | Invalid Param (sustainability) | `422` | `422` | ✅ PASS | FastAPI validation rules correctly rejected input. |
| Audit | `GET` | `/api/v1/audit/` | List Events Happy Path | `200` | `200` | ✅ PASS | Retrieved audit trails list. |
| Audit | `GET` | `/api/v1/audit/` | List Events Missing Auth | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Audit | `GET` | `/api/v1/audit/` | List Events Invalid Input | `422` | `422` | ✅ PASS | Expected validation failure for page < 1. |
| Audit | `GET` | `/api/v1/audit/stats` | Get Stats Happy Path | `200` | `200` | ✅ PASS | Retrieved audit statistics. |
| Audit | `GET` | `/api/v1/audit/stats` | Get Stats Missing Auth | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Audit | `GET` | `/api/v1/audit/stats` | Get Stats Invalid Input | `422` | `422` | ✅ PASS | Expected validation failure for bad period value. |
| Audit | `GET` | `/api/v1/audit/timeline` | Get Timeline Happy Path | `200` | `200` | ✅ PASS | Retrieved audit timeline. |
| Audit | `GET` | `/api/v1/audit/timeline` | Get Timeline Missing Auth | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Audit | `GET` | `/api/v1/audit/timeline` | Get Timeline Invalid Input | `422` | `422` | ✅ PASS | Expected validation failure for bad UUID. |
| Audit | `GET` | `/api/v1/audit/export` | Export Log Happy Path | `200` | `200` | ✅ PASS | Exported CSV file successfully. |
| Audit | `GET` | `/api/v1/audit/export` | Export Log Missing Auth | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Audit | `GET` | `/api/v1/audit/export` | Export Log Invalid Input | `400` | `400` | ✅ PASS | Expected 400 for unsupported format. |
| Audit | `GET` | `/api/v1/audit/{event_id}` | Get Event Happy Path | `200` | `200` | ✅ PASS | Successfully fetched specific event details. |
| Audit | `GET` | `/api/v1/audit/{event_id}` | Get Event Missing Auth | `401/403` | `401` | ✅ PASS | Correctly refused access. |
| Audit | `GET` | `/api/v1/audit/{event_id}` | Get Event Invalid Input | `422` | `422` | ✅ PASS | Expected validation failure for bad UUID. |
| Audit | `GET` | `/api/v1/audit/{event_id}` | Get Event Not Found | `404` | `404` | ✅ PASS | Expected 404 Not Found. |
| Auth | `POST` | `/api/v1/auth/logout` | Logout Happy Path | `200` | `200` | ✅ PASS | Revoked refresh token successfully. |

---

## Detailed Failed Test Cases Logs
All executed test cases passed successfully. No failures to log.
