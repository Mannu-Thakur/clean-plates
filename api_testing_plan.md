# CleanPlates Comprehensive API Testing Plan

## Agent Instructions
You are an autonomous API testing agent. The user will ask you to **"Execute round x"**. When this happens:
1. Find the section for **Round x** below.
2. Execute all the defined API tests within that round against the local development server (or configured environment).
3. You may use `curl`, Python `requests`, or an HTTP client of your choice to execute these tests.
4. **Multiple Inputs & Outputs Validation**: For every endpoint, test the **Valid/Happy Path**, **Missing Parameters/Payload**, and **Invalid Data Types/Values**. Observe the outputs and ensure they match the expected response structures (e.g., `200 OK`, `422 Unprocessable Entity`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`).
5. Ensure you authenticate properly (obtain JWT via the auth endpoint) before testing secured endpoints.
6. **After completing a round**, you MUST generate a detailed markdown report (`round_x_test_report.md`).
   - This report must list: **Issues Discovered**, **Test Cases Passed**, **Test Cases Failed**, and **Suggested Fixes** with code snippets if applicable.

## Round 1
**Endpoints Covered:** Analytics, Audit, Auth

### Tag: Analytics

#### `[GET]` `/api/v1/analytics/overview`
**Summary:** Get Overview

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"period": "30d", "date_from": "val", "date_to": "val", "student_id": "val", "device_id": "val", "branch": "val", "year": "val", "hostel": "val", "meal_type": "val", "food": "val", "status": "val"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/analytics/trends`
**Summary:** Get Trends

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"type": "weekly", "period": "30d", "date_from": "val", "date_to": "val", "student_id": "val", "device_id": "val", "branch": "val", "year": "val", "hostel": "val", "meal_type": "val", "food": "val", "status": "val"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/analytics/peaks`
**Summary:** Get Peak Waste

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"period": "30d", "date_from": "val", "date_to": "val", "student_id": "val", "device_id": "val", "branch": "val", "year": "val", "hostel": "val", "meal_type": "val", "food": "val", "status": "val"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/analytics/meal-distribution`
**Summary:** Get Meal Distribution

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"period": "30d", "date_from": "val", "date_to": "val", "student_id": "val", "device_id": "val", "branch": "val", "year": "val", "hostel": "val", "meal_type": "val", "food": "val", "status": "val"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/analytics/food-waste-distribution`
**Summary:** Get Food Waste Distribution

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"limit": 10, "period": "30d", "date_from": "val", "date_to": "val", "student_id": "val", "device_id": "val", "branch": "val", "year": "val", "hostel": "val", "meal_type": "val", "food": "val", "status": "val"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/analytics/top-waste-contributors`
**Summary:** Get Top Contributors

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"limit": 10, "period": "30d", "date_from": "val", "date_to": "val", "student_id": "val", "device_id": "val", "branch": "val", "year": "val", "hostel": "val", "meal_type": "val", "food": "val", "status": "val"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/analytics/improvement-tracking`
**Summary:** Get Improvement Tracking

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"period": "30d", "date_from": "val", "date_to": "val", "student_id": "val", "device_id": "val", "branch": "val", "year": "val", "hostel": "val", "meal_type": "val", "food": "val", "status": "val"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/analytics/sustainability`
**Summary:** Get Sustainability Scores

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"branch": "val", "year": "val", "hostel": "val", "status": "val"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

### Tag: Audit

#### `[GET]` `/api/v1/audit/`
**Summary:** List Events

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"user_id": "val", "event_type": "val", "resource_type": "val", "date_from": "val", "date_to": "val", "q": "val", "sort": "created_at", "order": "desc", "page": 1, "size": 25}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/audit/stats`
**Summary:** Get Stats

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"period": "today"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/audit/timeline`
**Summary:** Get Timeline

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"user_id": "val", "event_type": "val", "resource_type": "val", "date_from": "val", "date_to": "val", "q": "val"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/audit/export`
**Summary:** Export Log

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"user_id": "val", "event_type": "val", "resource_type": "val", "date_from": "val", "date_to": "val", "q": "val", "format": "csv"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/audit/{event_id}`
**Summary:** Get Event

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"event_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"event_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

### Tag: Auth

#### `[POST]` `/api/v1/auth/login`
**Summary:** Login

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "email": "test@example.com",
  "password": "sample_password",
  "remember_me": false
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "remember_me": false
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "email": 12345,
  "password": 12345,
  "remember_me": false
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[POST]` `/api/v1/auth/logout`
**Summary:** Logout

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "refresh_token": "sample_refresh_token"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "refresh_token": 12345
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[POST]` `/api/v1/auth/refresh`
**Summary:** Refresh Token

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "refresh_token": "sample_refresh_token"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "refresh_token": 12345
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[GET]` `/api/v1/auth/me`
**Summary:** Get Me

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[POST]` `/api/v1/auth/forgot-password`
**Summary:** Forgot Password

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "email": "test@example.com"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "email": 12345
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[POST]` `/api/v1/auth/reset-password`
**Summary:** Reset Password

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "token": "sample_token",
  "new_password": "sample_new_password"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "token": 12345,
  "new_password": 12345
}
```
- **Expected Output**: `422 Unprocessable Entity`

## Round 2
**Endpoints Covered:** Configuration, Devices, Email Templates

### Tag: Configuration

#### `[GET]` `/api/v1/config/institution`
**Summary:** Get Institution Config

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[PATCH]` `/api/v1/config/institution`
**Summary:** Update Institution Config

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "data": {}
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "data": null
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[GET]` `/api/v1/config/device`
**Summary:** Get Device Config

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[PATCH]` `/api/v1/config/device`
**Summary:** Update Device Config

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "data": {}
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "data": null
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[GET]` `/api/v1/config/thresholds`
**Summary:** Get Thresholds

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[PATCH]` `/api/v1/config/thresholds`
**Summary:** Update Thresholds

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "waste_threshold_grams": 150.0,
  "warning_threshold_grams": 100.0,
  "penalty_threshold_grams": 200.0,
  "improvement_target_pct": 25.0,
  "reset_duration_days": 30,
  "warning_count_for_penalty": 5
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "waste_threshold_grams": 150.0,
  "warning_threshold_grams": 100.0,
  "penalty_threshold_grams": 200.0,
  "improvement_target_pct": 25.0,
  "reset_duration_days": 30,
  "warning_count_for_penalty": 5
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[GET]` `/api/v1/config/meals`
**Summary:** Get Meal Timings

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[PUT]` `/api/v1/config/meals`
**Summary:** Update Meal Timings

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[GET]` `/api/v1/config/branches`
**Summary:** Get Branches

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[PUT]` `/api/v1/config/branches`
**Summary:** Update Branches

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[GET]` `/api/v1/config/system`
**Summary:** Get System Policies

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[PATCH]` `/api/v1/config/system`
**Summary:** Update System Policies

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "sync_frequency_minutes": 5,
  "offline_handling": "queue",
  "backup_interval_hours": 24,
  "data_retention_days": 365,
  "log_retention_days": 30,
  "audit_retention_days": 90
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "sync_frequency_minutes": 5,
  "offline_handling": "queue",
  "backup_interval_hours": 24,
  "data_retention_days": 365,
  "log_retention_days": 30,
  "audit_retention_days": 90
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[POST]` `/api/v1/config/reset/{section}`
**Summary:** Reset Defaults

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"section": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"section": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

### Tag: Devices

#### `[GET]` `/api/v1/devices/`
**Summary:** List Devices

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"status": "val", "page": 1, "size": 20}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[POST]` `/api/v1/devices/`
**Summary:** Register Device

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "device_serial": "sample_device_serial",
  "edge_node_name": "sample_edge_node_name",
  "institution_name": "sample_institution_name",
  "institution_code": "sample_institution_code",
  "campus_name": "sample_campus_name",
  "mess_name": "sample_mess_name",
  "mess_id": "sample_mess_id",
  "hostel_name": "sample_hostel_name",
  "hostel_block": "sample_hostel_block",
  "floor_number": "sample_floor_number",
  "wing_section": "sample_wing_section",
  "capacity": "sample_capacity",
  "meal_capacity_per_day": "sample_meal_capacity_per_day",
  "managed_by": "sample_managed_by",
  "admin_contact": "sample_admin_contact"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "hostel_name": "sample_hostel_name",
  "hostel_block": "sample_hostel_block",
  "floor_number": "sample_floor_number",
  "wing_section": "sample_wing_section",
  "capacity": "sample_capacity",
  "meal_capacity_per_day": "sample_meal_capacity_per_day",
  "managed_by": "sample_managed_by",
  "admin_contact": "sample_admin_contact"
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "device_serial": 12345,
  "edge_node_name": 12345,
  "institution_name": 12345,
  "institution_code": 12345,
  "campus_name": 12345,
  "mess_name": 12345,
  "mess_id": 12345,
  "hostel_name": "sample_hostel_name",
  "hostel_block": "sample_hostel_block",
  "floor_number": "sample_floor_number",
  "wing_section": "sample_wing_section",
  "capacity": "sample_capacity",
  "meal_capacity_per_day": "sample_meal_capacity_per_day",
  "managed_by": "sample_managed_by",
  "admin_contact": "sample_admin_contact"
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[GET]` `/api/v1/devices/{device_id}`
**Summary:** Get Device

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"device_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"device_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[PATCH]` `/api/v1/devices/{device_id}`
**Summary:** Update Device

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"device_id": "string_id"}`
- **Request Body**:
```json
{
  "edge_node_name": "sample_edge_node_name",
  "mess_name": "sample_mess_name",
  "hostel_name": "sample_hostel_name",
  "hostel_block": "sample_hostel_block",
  "floor_number": "sample_floor_number",
  "capacity": "sample_capacity"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "edge_node_name": "sample_edge_node_name",
  "mess_name": "sample_mess_name",
  "hostel_name": "sample_hostel_name",
  "hostel_block": "sample_hostel_block",
  "floor_number": "sample_floor_number",
  "capacity": "sample_capacity"
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"device_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/devices/{device_id}/health`
**Summary:** Get Device Health

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"device_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"device_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/devices/{device_id}/health/history`
**Summary:** Get Health History

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"device_id": "string_id"}`
- **Query Parameters**: `{"period": "24h"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"device_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[POST]` `/api/v1/devices/{device_id}/sync`
**Summary:** Trigger Sync

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"device_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"device_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[POST]` `/api/v1/devices/{device_id}/restart`
**Summary:** Restart Service

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"device_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"device_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[POST]` `/api/v1/devices/{device_id}/decommission`
**Summary:** Decommission

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"device_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"device_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

### Tag: Email Templates

#### `[GET]` `/api/v1/templates/`
**Summary:** List Templates

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"type": "val"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[POST]` `/api/v1/templates/`
**Summary:** Create Template

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "name": "sample_name",
  "type": "sample_type",
  "subject": "sample_subject",
  "body_html": "sample_body_html",
  "variables": []
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "variables": []
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "name": 12345,
  "type": 12345,
  "subject": 12345,
  "body_html": 12345,
  "variables": []
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[GET]` `/api/v1/templates/{template_id}`
**Summary:** Get Template

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"template_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"template_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[PATCH]` `/api/v1/templates/{template_id}`
**Summary:** Update Template

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"template_id": "string_id"}`
- **Request Body**:
```json
{
  "name": "sample_name",
  "subject": "sample_subject",
  "body_html": "sample_body_html",
  "variables": "sample_variables"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "name": "sample_name",
  "subject": "sample_subject",
  "body_html": "sample_body_html",
  "variables": "sample_variables"
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"template_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[DELETE]` `/api/v1/templates/{template_id}`
**Summary:** Delete Template

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"template_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"template_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[POST]` `/api/v1/templates/{template_id}/preview`
**Summary:** Preview Template

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"template_id": "string_id"}`
- **Request Body**:
```json
{
  "variables": {}
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "variables": {}
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"template_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

## Round 3
**Endpoints Covered:** Filter Presets, Health, ML Ingestion

### Tag: Filter Presets

#### `[GET]` `/api/v1/filters/presets`
**Summary:** List Presets

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[POST]` `/api/v1/filters/presets`
**Summary:** Save Preset

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "name": "sample_name",
  "filter_state": {}
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "filter_state": {}
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "name": 12345,
  "filter_state": {}
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[GET]` `/api/v1/filters/presets/{preset_id}`
**Summary:** Get Preset

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"preset_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"preset_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[PATCH]` `/api/v1/filters/presets/{preset_id}`
**Summary:** Update Preset

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"preset_id": "string_id"}`
- **Request Body**:
```json
{
  "name": "sample_name",
  "filter_state": "sample_filter_state"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "name": "sample_name",
  "filter_state": "sample_filter_state"
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"preset_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[DELETE]` `/api/v1/filters/presets/{preset_id}`
**Summary:** Delete Preset

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"preset_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"preset_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

### Tag: Health

#### `[GET]` `/health`
**Summary:** Health Check

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

### Tag: ML Ingestion

#### `[POST]` `/api/v1/ml/detect`
**Summary:** Ingest Detection

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "student_device_id": "sample_student_device_id",
  "device_serial": "sample_device_serial",
  "weight_grams": 1.0,
  "meal_type": "sample_meal_type",
  "food_items": [],
  "confidence_score": "sample_confidence_score",
  "plate_image_path": "sample_plate_image_path",
  "timestamp": "2023-10-01T12:00:00Z"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "meal_type": "sample_meal_type",
  "food_items": [],
  "confidence_score": "sample_confidence_score",
  "plate_image_path": "sample_plate_image_path"
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "student_device_id": 12345,
  "device_serial": 12345,
  "weight_grams": null,
  "meal_type": "sample_meal_type",
  "food_items": [],
  "confidence_score": "sample_confidence_score",
  "plate_image_path": "sample_plate_image_path",
  "timestamp": 12345
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[POST]` `/api/v1/ml/sync`
**Summary:** Bulk Ingest

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "entries": []
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "entries": "not_an_array"
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[POST]` `/api/v1/ml/heartbeat`
**Summary:** Ml Heartbeat

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "cpu_percent": 1.0,
  "ram_percent": 1.0,
  "temperature": "sample_temperature",
  "storage_percent": "sample_storage_percent",
  "connectivity": true
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "temperature": "sample_temperature",
  "storage_percent": "sample_storage_percent",
  "connectivity": true
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "cpu_percent": null,
  "ram_percent": null,
  "temperature": "sample_temperature",
  "storage_percent": "sample_storage_percent",
  "connectivity": true
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[POST]` `/api/v1/ml/upload-image`
**Summary:** Upload Image

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "image_file": "sample_image_file"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "image_file": 12345
}
```
- **Expected Output**: `422 Unprocessable Entity`

## Round 4
**Endpoints Covered:** Monitoring, Notifications, Reports

### Tag: Monitoring

#### `[GET]` `/api/v1/monitoring/current-session`
**Summary:** Get Current Session

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"device_id": "val"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/monitoring/recent-entries`
**Summary:** Get Recent Entries

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"device_id": "val", "limit": 20}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/monitoring/device-statuses`
**Summary:** Get Device Statuses

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[POST]` `/api/v1/monitoring/alerts/{notif_id}/acknowledge`
**Summary:** Acknowledge Alert

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"notif_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"notif_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

### Tag: Notifications

#### `[GET]` `/api/v1/notifications/`
**Summary:** List Notifications

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"tab": "val", "type": "val", "channel": "val", "page": 1, "size": 20}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[POST]` `/api/v1/notifications/`
**Summary:** Send Notification

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "type": "sample_type",
  "channel": "sample_channel",
  "subject": "sample_subject",
  "body": "sample_body",
  "recipient_type": "sample_recipient_type",
  "recipient_ids": [],
  "template_id": "sample_template_id"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "recipient_ids": [],
  "template_id": "sample_template_id"
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "type": 12345,
  "channel": 12345,
  "subject": 12345,
  "body": 12345,
  "recipient_type": 12345,
  "recipient_ids": [],
  "template_id": "sample_template_id"
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[GET]` `/api/v1/notifications/stats`
**Summary:** Get Notification Stats

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[POST]` `/api/v1/notifications/broadcast`
**Summary:** Send Broadcast

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "subject": "sample_subject",
  "body": "sample_body",
  "channel": "sample_channel",
  "recipient_type": "sample_recipient_type",
  "recipient_filter": {},
  "template_id": "sample_template_id"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "recipient_filter": {},
  "template_id": "sample_template_id"
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "subject": 12345,
  "body": 12345,
  "channel": 12345,
  "recipient_type": 12345,
  "recipient_filter": {},
  "template_id": "sample_template_id"
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[POST]` `/api/v1/notifications/schedule`
**Summary:** Schedule Notification

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "type": "sample_type",
  "channel": "sample_channel",
  "subject": "sample_subject",
  "body": "sample_body",
  "recipient_type": "sample_recipient_type",
  "recipient_ids": [],
  "template_id": "sample_template_id",
  "scheduled_at": "2023-10-01T12:00:00Z"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "recipient_ids": [],
  "template_id": "sample_template_id"
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "type": 12345,
  "channel": 12345,
  "subject": 12345,
  "body": 12345,
  "recipient_type": 12345,
  "recipient_ids": [],
  "template_id": "sample_template_id",
  "scheduled_at": 12345
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[POST]` `/api/v1/notifications/mark-all-read`
**Summary:** Mark All Read

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/notifications/{notif_id}/delivery`
**Summary:** Get Delivery Status

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"notif_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"notif_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/notifications/{notif_id}`
**Summary:** Get Notification

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"notif_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"notif_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[DELETE]` `/api/v1/notifications/{notif_id}`
**Summary:** Delete Notification

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"notif_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"notif_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[PATCH]` `/api/v1/notifications/{notif_id}/read`
**Summary:** Mark Read

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"notif_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"notif_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[POST]` `/api/v1/notifications/{notif_id}/retry`
**Summary:** Retry Failed

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"notif_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"notif_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

### Tag: Reports

#### `[GET]` `/api/v1/reports/`
**Summary:** List Reports

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"type": "val", "date_from": "val", "date_to": "val", "page": 1, "size": 20}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[POST]` `/api/v1/reports/generate`
**Summary:** Generate Report

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "type": "sample_type",
  "format": "sample_format",
  "date_from": "sample_date_from",
  "date_to": "sample_date_to",
  "student_id": "sample_student_id",
  "filters": {}
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "date_from": "sample_date_from",
  "date_to": "sample_date_to",
  "student_id": "sample_student_id",
  "filters": {}
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "type": 12345,
  "format": 12345,
  "date_from": "sample_date_from",
  "date_to": "sample_date_to",
  "student_id": "sample_student_id",
  "filters": {}
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[GET]` `/api/v1/reports/schedules`
**Summary:** List Schedules

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[POST]` `/api/v1/reports/schedules`
**Summary:** Create Schedule

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "report_type": "sample_report_type",
  "format": "sample_format",
  "frequency": "sample_frequency",
  "day_of_week": "sample_day_of_week",
  "time_of_day": "sample_time_of_day",
  "email_recipients": [],
  "auto_email": false,
  "active": true
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "day_of_week": "sample_day_of_week",
  "email_recipients": [],
  "auto_email": false,
  "active": true
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "report_type": 12345,
  "format": 12345,
  "frequency": 12345,
  "day_of_week": "sample_day_of_week",
  "time_of_day": 12345,
  "email_recipients": [],
  "auto_email": false,
  "active": true
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[PATCH]` `/api/v1/reports/schedules/{schedule_id}`
**Summary:** Update Schedule

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"schedule_id": "string_id"}`
- **Request Body**:
```json
{
  "report_type": "sample_report_type",
  "format": "sample_format",
  "frequency": "sample_frequency",
  "day_of_week": "sample_day_of_week",
  "time_of_day": "sample_time_of_day",
  "email_recipients": "sample_email_recipients",
  "auto_email": "sample_auto_email",
  "active": "sample_active"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "report_type": "sample_report_type",
  "format": "sample_format",
  "frequency": "sample_frequency",
  "day_of_week": "sample_day_of_week",
  "time_of_day": "sample_time_of_day",
  "email_recipients": "sample_email_recipients",
  "auto_email": "sample_auto_email",
  "active": "sample_active"
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"schedule_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[DELETE]` `/api/v1/reports/schedules/{schedule_id}`
**Summary:** Delete Schedule

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"schedule_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"schedule_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/reports/{report_id}/download`
**Summary:** Download Report

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"report_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"report_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[DELETE]` `/api/v1/reports/{report_id}`
**Summary:** Delete Report

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"report_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"report_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

## Round 5
**Endpoints Covered:** Roles, Rules, Settings

### Tag: Roles

#### `[GET]` `/api/v1/roles/`
**Summary:** List Roles

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[PATCH]` `/api/v1/roles/{role_id}`
**Summary:** Update Role

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"role_id": "string_id"}`
- **Request Body**:
```json
{
  "permissions": {},
  "description": "sample_description"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "permissions": {},
  "description": "sample_description"
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"role_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

### Tag: Rules

#### `[GET]` `/api/v1/rules/`
**Summary:** List Rules

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"type": "val", "priority": "val", "status": "val", "sort": "created_at", "order": "desc", "page": 1, "size": 20}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[POST]` `/api/v1/rules/`
**Summary:** Create Rule

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "name": "sample_name",
  "description": "sample_description",
  "type": "sample_type",
  "priority": "sample_priority",
  "active": true,
  "conditions": [],
  "time_constraints": "sample_time_constraints",
  "scope": {},
  "actions": [],
  "chain_to_rule_id": "sample_chain_to_rule_id"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "description": "sample_description",
  "active": true,
  "time_constraints": "sample_time_constraints",
  "scope": {},
  "chain_to_rule_id": "sample_chain_to_rule_id"
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "name": 12345,
  "description": "sample_description",
  "type": 12345,
  "priority": 12345,
  "active": true,
  "conditions": "not_an_array",
  "time_constraints": "sample_time_constraints",
  "scope": {},
  "actions": "not_an_array",
  "chain_to_rule_id": "sample_chain_to_rule_id"
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[GET]` `/api/v1/rules/metadata/fields`
**Summary:** Get Available Fields

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/rules/metadata/operators`
**Summary:** Get Available Operators

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/rules/metadata/actions`
**Summary:** Get Available Actions

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/rules/chains`
**Summary:** Get Rule Chains

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/rules/{rule_id}`
**Summary:** Get Rule

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"rule_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"rule_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[PATCH]` `/api/v1/rules/{rule_id}`
**Summary:** Update Rule

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"rule_id": "string_id"}`
- **Request Body**:
```json
{
  "name": "sample_name",
  "description": "sample_description",
  "priority": "sample_priority",
  "active": "sample_active",
  "conditions": "sample_conditions",
  "time_constraints": "sample_time_constraints",
  "scope": "sample_scope",
  "actions": "sample_actions",
  "chain_to_rule_id": "sample_chain_to_rule_id"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "name": "sample_name",
  "description": "sample_description",
  "priority": "sample_priority",
  "active": "sample_active",
  "conditions": "sample_conditions",
  "time_constraints": "sample_time_constraints",
  "scope": "sample_scope",
  "actions": "sample_actions",
  "chain_to_rule_id": "sample_chain_to_rule_id"
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"rule_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[DELETE]` `/api/v1/rules/{rule_id}`
**Summary:** Delete Rule

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"rule_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"rule_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[POST]` `/api/v1/rules/{rule_id}/toggle`
**Summary:** Toggle Rule

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"rule_id": "string_id"}`
- **Request Body**:
```json
{
  "active": true
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "active": "not_a_bool"
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"rule_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[POST]` `/api/v1/rules/{rule_id}/duplicate`
**Summary:** Duplicate Rule

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"rule_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"rule_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[POST]` `/api/v1/rules/{rule_id}/test`
**Summary:** Test Rule

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"rule_id": "string_id"}`
- **Request Body**:
```json
{
  "waste_grams": "sample_waste_grams",
  "meal_type": "sample_meal_type",
  "severity": "sample_severity",
  "student_branch": "sample_student_branch",
  "student_year": "sample_student_year",
  "frequency_count": "sample_frequency_count",
  "warning_count": "sample_warning_count",
  "penalty_count": "sample_penalty_count",
  "sustainability_score": "sample_sustainability_score"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "waste_grams": "sample_waste_grams",
  "meal_type": "sample_meal_type",
  "severity": "sample_severity",
  "student_branch": "sample_student_branch",
  "student_year": "sample_student_year",
  "frequency_count": "sample_frequency_count",
  "warning_count": "sample_warning_count",
  "penalty_count": "sample_penalty_count",
  "sustainability_score": "sample_sustainability_score"
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"rule_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[POST]` `/api/v1/rules/{rule_id}/simulate`
**Summary:** Simulate Rule

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"rule_id": "string_id"}`
- **Query Parameters**: `{"date_from": "val", "date_to": "val"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"rule_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/rules/{rule_id}/executions`
**Summary:** Get Rule Executions

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"rule_id": "string_id"}`
- **Query Parameters**: `{"page": 1, "size": 20}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"rule_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

### Tag: Settings

#### `[GET]` `/api/v1/settings/users`
**Summary:** List Users

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[POST]` `/api/v1/settings/users`
**Summary:** Create User

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "email": "test@example.com",
  "name": "sample_name",
  "role": "sample_role",
  "password": "sample_password"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "password": "sample_password"
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "email": 12345,
  "name": 12345,
  "role": 12345,
  "password": "sample_password"
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[PATCH]` `/api/v1/settings/users/{user_id}`
**Summary:** Update User

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"user_id": "string_id"}`
- **Request Body**:
```json
{
  "name": "sample_name",
  "role": "sample_role",
  "email": "sample_email"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "name": "sample_name",
  "role": "sample_role",
  "email": "sample_email"
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"user_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[POST]` `/api/v1/settings/users/{user_id}/deactivate`
**Summary:** Deactivate User

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"user_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"user_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[POST]` `/api/v1/settings/users/{user_id}/reset-password`
**Summary:** Reset User Password

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"user_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"user_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/settings/security`
**Summary:** Get Security Config

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[PATCH]` `/api/v1/settings/security`
**Summary:** Update Security Config

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "access_token_expiry_minutes": 60,
  "refresh_token_expiry_days": 7,
  "min_password_length": 8,
  "require_uppercase": true,
  "require_numbers": true,
  "max_login_attempts": 5,
  "lockout_duration_minutes": 15,
  "session_timeout_minutes": 120
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "access_token_expiry_minutes": 60,
  "refresh_token_expiry_days": 7,
  "min_password_length": 8,
  "require_uppercase": true,
  "require_numbers": true,
  "max_login_attempts": 5,
  "lockout_duration_minutes": 15,
  "session_timeout_minutes": 120
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[GET]` `/api/v1/settings/backups`
**Summary:** List Backups

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[POST]` `/api/v1/settings/backups`
**Summary:** Trigger Backup

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[POST]` `/api/v1/settings/backups/restore`
**Summary:** Restore Backup

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "backup_file": "sample_backup_file"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "backup_file": 12345
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[GET]` `/api/v1/settings/backups/{backup_id}/download`
**Summary:** Download Backup

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"backup_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"backup_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/settings/appearance`
**Summary:** Get Appearance

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[PATCH]` `/api/v1/settings/appearance`
**Summary:** Update Appearance

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "theme": "dark",
  "logo_path": "sample_logo_path",
  "primary_color": "#6366f1",
  "institution_display_name": "sample_institution_display_name"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "theme": "dark",
  "logo_path": "sample_logo_path",
  "primary_color": "#6366f1",
  "institution_display_name": "sample_institution_display_name"
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[POST]` `/api/v1/settings/appearance/logo`
**Summary:** Upload Logo

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "image_file": "sample_image_file"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "image_file": 12345
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[POST]` `/api/v1/settings/maintenance/clear-cache`
**Summary:** Clear Cache

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[POST]` `/api/v1/settings/maintenance/optimize-db`
**Summary:** Optimize Db

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/settings/maintenance/system-info`
**Summary:** Get System Info

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/settings/maintenance/export-all`
**Summary:** Export All Data

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

## Round 6
**Endpoints Covered:** Students, Warnings, Waste

### Tag: Students

#### `[GET]` `/api/v1/students/`
**Summary:** List Students

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"status": "val", "hostel": "val", "branch": "val", "year": "val", "page": 1, "size": 20, "sort": "created_at", "order": "desc"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/students/export`
**Summary:** Export Students

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"format": "csv", "status": "val", "hostel": "val", "branch": "val", "year": "val", "sort": "created_at", "order": "desc"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[POST]` `/api/v1/students/import-mapping`
**Summary:** Import Mapping Csv

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "csv_file": "sample_csv_file"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "csv_file": 12345
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[POST]` `/api/v1/students/bulk/warn`
**Summary:** Bulk Warn

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "student_ids": [],
  "reason": "sample_reason",
  "level": "level_1",
  "send_email": false
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "level": "level_1",
  "send_email": false
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "student_ids": "not_an_array",
  "reason": 12345,
  "level": "level_1",
  "send_email": false
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[GET]` `/api/v1/students/{student_id}`
**Summary:** Get Student

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"student_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"student_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[PATCH]` `/api/v1/students/{student_id}`
**Summary:** Update Student Profile

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"student_id": "string_id"}`
- **Request Body**:
```json
{
  "is_active": "sample_is_active"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "is_active": "sample_is_active"
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"student_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[POST]` `/api/v1/students/{student_id}/map`
**Summary:** Map Student Id

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"student_id": "string_id"}`
- **Request Body**:
```json
{
  "name": "sample_name",
  "roll_number": "sample_roll_number",
  "branch": "sample_branch",
  "year": 1,
  "hostel": "sample_hostel",
  "room_number": "sample_room_number",
  "email": "sample_email"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "hostel": "sample_hostel",
  "room_number": "sample_room_number",
  "email": "sample_email"
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "name": 12345,
  "roll_number": 12345,
  "branch": 12345,
  "year": "invalid_int_string",
  "hostel": "sample_hostel",
  "room_number": "sample_room_number",
  "email": "sample_email"
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"student_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[PATCH]` `/api/v1/students/{student_id}/map`
**Summary:** Update Mapping

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"student_id": "string_id"}`
- **Request Body**:
```json
{
  "name": "sample_name",
  "roll_number": "sample_roll_number",
  "branch": "sample_branch",
  "year": "sample_year",
  "hostel": "sample_hostel",
  "room_number": "sample_room_number",
  "email": "sample_email"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "name": "sample_name",
  "roll_number": "sample_roll_number",
  "branch": "sample_branch",
  "year": "sample_year",
  "hostel": "sample_hostel",
  "room_number": "sample_room_number",
  "email": "sample_email"
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"student_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/students/{student_id}/stats`
**Summary:** Get Student Stats

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"student_id": "string_id"}`
- **Query Parameters**: `{"period": "30d"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"student_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/students/{student_id}/timeline`
**Summary:** Get Student Timeline

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"student_id": "string_id"}`
- **Query Parameters**: `{"period": "30d"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"student_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/students/{student_id}/food-breakdown`
**Summary:** Get Food Breakdown

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"student_id": "string_id"}`
- **Query Parameters**: `{"period": "30d"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"student_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/students/{student_id}/meal-pattern`
**Summary:** Get Meal Pattern

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"student_id": "string_id"}`
- **Query Parameters**: `{"period": "30d"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"student_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/students/{student_id}/improvement`
**Summary:** Get Improvement Trend

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"student_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"student_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/students/{student_id}/history`
**Summary:** Get Student History

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"student_id": "string_id"}`
- **Query Parameters**: `{"page": 1, "size": 20}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"student_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/students/{student_id}/warnings`
**Summary:** Get Student Warnings

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"student_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"student_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[POST]` `/api/v1/students/{student_id}/warnings`
**Summary:** Create Warning

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"student_id": "string_id"}`
- **Request Body**:
```json
{
  "level": "sample_level",
  "reason": "sample_reason",
  "send_email": false,
  "rule_id": "sample_rule_id",
  "waste_entry_id": "sample_waste_entry_id"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "send_email": false,
  "rule_id": "sample_rule_id",
  "waste_entry_id": "sample_waste_entry_id"
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "level": 12345,
  "reason": 12345,
  "send_email": false,
  "rule_id": "sample_rule_id",
  "waste_entry_id": "sample_waste_entry_id"
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"student_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[POST]` `/api/v1/students/{student_id}/penalties`
**Summary:** Create Penalty Direct

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"student_id": "string_id"}`
- **Request Body**:
```json
{
  "points": 1,
  "reason": "sample_reason",
  "send_email": false,
  "rule_id": "sample_rule_id"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "send_email": false,
  "rule_id": "sample_rule_id"
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "points": "invalid_int_string",
  "reason": 12345,
  "send_email": false,
  "rule_id": "sample_rule_id"
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"student_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

### Tag: Warnings

#### `[GET]` `/api/v1/warnings/`
**Summary:** List Warnings

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"status": "val", "level": "val", "student_id": "val", "date_from": "val", "date_to": "val", "page": 1, "size": 20}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/warnings/stats`
**Summary:** Get Warning Stats

**Test Case 1: Valid Input (Happy Path)**
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/warnings/export`
**Summary:** Export Warnings

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"format": "val", "status": "val", "level": "val", "student_id": "val", "date_from": "val", "date_to": "val"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[PATCH]` `/api/v1/warnings/bulk/resolve`
**Summary:** Bulk Resolve

**Test Case 1: Valid Input (Happy Path)**
- **Request Body**:
```json
{
  "warning_ids": [],
  "resolution_note": "sample_resolution_note"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "warning_ids": "not_an_array",
  "resolution_note": 12345
}
```
- **Expected Output**: `422 Unprocessable Entity`

#### `[PATCH]` `/api/v1/warnings/{warning_id}/resolve`
**Summary:** Resolve Warning

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"warning_id": "string_id"}`
- **Request Body**:
```json
{
  "resolution_note": "sample_resolution_note"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "resolution_note": 12345
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"warning_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[POST]` `/api/v1/warnings/{warning_id}/escalate`
**Summary:** Escalate Warning

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"warning_id": "string_id"}`
- **Request Body**:
```json
{
  "escalated_to_role": "sample_escalated_to_role",
  "reason": "sample_reason"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "escalated_to_role": 12345,
  "reason": 12345
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"warning_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[POST]` `/api/v1/warnings/{warning_id}/apply-penalty`
**Summary:** Apply Penalty

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"warning_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"warning_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/penalties/`
**Summary:** List Penalties

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"status": "val", "student_id": "val", "page": 1, "size": 20}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[PATCH]` `/api/v1/penalties/{penalty_id}/revoke`
**Summary:** Revoke Penalty

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"penalty_id": "string_id"}`
- **Request Body**:
```json
{
  "reason": "sample_reason"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "reason": 12345
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"penalty_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/escalations/`
**Summary:** List Escalations

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"status": "val"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[POST]` `/api/v1/escalations/{escalation_id}/review`
**Summary:** Review Escalation

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"escalation_id": "string_id"}`
- **Request Body**:
```json
{
  "decision": "sample_decision",
  "review_note": "sample_review_note"
}
```
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Request Body (Missing Required)**:
```json
{
  "review_note": "sample_review_note"
}
```
- **Expected Output**: `422 Unprocessable Entity` (Validation Error)

**Test Case 3: Invalid Data Types**
- **Request Body (Invalid Types)**:
```json
{
  "decision": 12345,
  "review_note": "sample_review_note"
}
```
- **Expected Output**: `422 Unprocessable Entity`

**Test Case 4: Not Found**
- **Path Parameters**: `{"escalation_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

### Tag: Waste

#### `[GET]` `/api/v1/waste/entries`
**Summary:** List Entries

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"student_id": "val", "device_id": "val", "meal_type": "val", "date_from": "val", "date_to": "val", "page": 1, "size": 20}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/waste/entries/{entry_id}`
**Summary:** Get Entry

**Test Case 1: Valid Input (Happy Path)**
- **Path Parameters**: `{"entry_id": "string_id"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

**Test Case 4: Not Found**
- **Path Parameters**: `{"entry_id": "non_existent_id"}`
- **Expected Output**: `404 Not Found`

#### `[GET]` `/api/v1/waste/current-session`
**Summary:** Get Current Session

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"device_id": "val"}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`

#### `[GET]` `/api/v1/waste/recent`
**Summary:** Get Recent Entries

**Test Case 1: Valid Input (Happy Path)**
- **Query Parameters**: `{"device_id": "val", "limit": 20}`
- **Expected Output**: `200 OK` or `201 Created` with expected response schema.

**Test Case 2: Missing Required Fields/Auth**
- **Action**: Perform request without Authorization header.
- **Expected Output**: `401 Unauthorized`
