# CleanPlates — Middlewares & Cross-Cutting Concerns

**Stack:** FastAPI + Starlette middleware stack

---

## 1. AuthMiddleware (JWT Dependency)
**File:** `app/middleware/auth.py`  
**Type:** FastAPI Dependency (not Starlette middleware)  
**Applied via:** `Depends(get_current_user)` on protected routes

**Logic:**
1. Extract `Authorization: Bearer <token>` header → 401 if missing
2. Decode JWT using `python-jose` → 401 if expired or invalid
3. Fetch user from DB by `user_id` from payload → 401 if not found or `is_active=False`
4. Return `CurrentUser` object to route handler

**Functions:**
- `get_current_user(token) → UserSchema` — Standard JWT auth dependency
- `get_current_user_optional(token?) → UserSchema | None` — For WebSocket (token in query param)
- `get_api_key_device(api_key) → DeviceSchema` — For ML pipeline routes; hash and match against `devices.api_key_hash`

---

## 2. RBACMiddleware (Role-Based Access)
**File:** `app/middleware/rbac.py`  
**Type:** FastAPI Dependency

**Functions:**
- `require_roles(*roles) → Depends` — Factory that returns a dependency checking `current_user.role in roles`; raises 403 if not
- `require_admin` — Shortcut: `require_roles("super_admin", "institution_admin")`
- `require_write_access` — Shortcut: blocks `analytics_viewer` from write routes

**Usage example:**
```python
@router.post("/rules", dependencies=[Depends(require_roles("super_admin", "institution_admin"))])
```

---

## 3. RequestLoggingMiddleware
**File:** `app/middleware/logging.py`  
**Type:** Starlette `BaseHTTPMiddleware`

**Logic:**
1. Log incoming request: `method`, `path`, `user_agent`, `ip`, `user_id` (if authenticated)
2. Process request
3. Log response: `status_code`, `duration_ms`
4. Format: structured JSON to `app.log`

**Config:** Skip logging for `/health`, `/metrics`, `/ws/*` to reduce noise

---

## 4. CORSMiddleware
**File:** `app/main.py` (registered on app)  
**Type:** Starlette `CORSMiddleware`

**Config:**
- `allow_origins`: From `settings.CORS_ORIGINS` (e.g., `["http://localhost:5173"]` for dev, dashboard domain for prod)
- `allow_credentials`: `True`
- `allow_methods`: `["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"]`
- `allow_headers`: `["Authorization", "Content-Type", "X-API-Key"]`

---

## 5. RateLimitMiddleware
**File:** `app/middleware/rate_limit.py`  
**Type:** Starlette `BaseHTTPMiddleware`  
**Backend:** Redis `INCR` + `EXPIRE`

**Limits:**

| Route Pattern | Limit | Window | Key |
|--------------|-------|--------|-----|
| `POST /auth/login` | 10 requests | 1 minute | IP address |
| `POST /auth/forgot-password` | 5 requests | 5 minutes | IP address |
| `/api/v1/*` (general) | 200 requests | 1 minute | `user_id` or IP |
| `/ml/*` (ML ingestion) | 1000 requests | 1 minute | `device_id` (API key) |
| `POST /reports/generate` | 5 requests | 5 minutes | `user_id` |

**On limit exceeded:** Return `429 Too Many Requests` with `Retry-After` header

---

## 6. AuditMiddleware
**File:** `app/middleware/audit.py`  
**Type:** FastAPI Dependency (injected per route via `Depends`)

**Logic:** Not a blanket middleware — routes that need auditing explicitly call `AuditService.log()` within their service layer. This keeps audit context (before/after state) accurate.

**AuditContext helper:**
- `capture_before(model_instance) → JSON` — Serialize model state before mutation
- `capture_after(model_instance) → JSON` — Serialize after mutation
- Both called within service functions, not middleware

---

## 7. ErrorHandlerMiddleware
**File:** `app/middleware/error_handler.py`  
**Type:** FastAPI `@app.exception_handler`

**Handlers:**

| Exception | HTTP Status | Response |
|-----------|-------------|----------|
| `HTTPException` | As specified | `{"detail": message}` |
| `RequestValidationError` | 422 | `{"detail": errors[], "body": input}` |
| `SQLAlchemyError` | 500 | `{"detail": "Database error"}` (log full error) |
| `FileNotFoundError` | 404 | `{"detail": "File not found"}` |
| `ValueError` | 400 | `{"detail": message}` |
| `PermissionError` | 403 | `{"detail": "Access denied"}` |
| `Exception` (catch-all) | 500 | `{"detail": "Internal server error"}` (log full traceback) |

All 5xx errors are logged with full traceback to structured log.

---

## 8. CompressionMiddleware
**File:** `app/main.py` (registered on app)  
**Type:** Starlette `GZipMiddleware`

**Config:**
- `minimum_size`: 1000 bytes (don't compress tiny responses)
- Applied to all routes except `/ws/*` (WebSocket incompatible)

---

## 9. TrustedHostMiddleware
**File:** `app/main.py`  
**Type:** Starlette `TrustedHostMiddleware`

**Config:**
- `allowed_hosts`: From `settings.ALLOWED_HOSTS` (e.g., `["localhost", "*.cloudflare.com", "yourdomain.com"]`)
- Rejects requests with invalid `Host` header → 400

---

## 10. SecurityHeadersMiddleware
**File:** `app/middleware/security_headers.py`  
**Type:** Starlette `BaseHTTPMiddleware`

**Headers added to every response:**

| Header | Value |
|--------|-------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` (HTTPS only) |

---

## 11. WebSocket AuthMiddleware
**File:** `app/middleware/ws_auth.py`  
**Type:** Custom dependency used in WS route handlers

**Logic:**
1. Extract `token` from WebSocket query param (`?token=<jwt>`)
2. Decode and validate JWT
3. Return user or close WebSocket with code 4001 (Unauthorized)
4. If user disconnects mid-stream → remove from room → clean up subscriptions

---

## 12. DatabaseSessionMiddleware
**File:** `app/middleware/db.py`  
**Type:** FastAPI Dependency

**Functions:**
- `get_db_session() → AsyncSession` — Yields SQLAlchemy async session; commits on success, rolls back on exception, closes always
- Used via `Depends(get_db_session)` in all route handlers and services

---

## Middleware Registration Order
**File:** `app/main.py`

```python
# Registration order matters in Starlette (outermost first)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CORSMiddleware, ...)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)
# Error handlers registered via @app.exception_handler
# Auth, RBAC, DB session via Depends() on each route
```

---

## Dependency Injection Map

| Route Type | Dependencies Used |
|------------|------------------|
| Public routes (login, forgot-pwd) | `RateLimitMiddleware` only |
| Protected read routes | `get_current_user`, `get_db_session`, `require_roles(...)` |
| Protected write routes | `get_current_user`, `get_db_session`, `require_roles(...)` + audit in service |
| ML ingestion routes | `get_api_key_device`, `get_db_session`, `RateLimitMiddleware` |
| WebSocket routes | `get_current_user_optional` (query param token), `get_db_session` |
| Admin-only routes | `get_current_user`, `require_roles("super_admin")` |

---

## Pydantic Settings
**File:** `app/core/config.py`

```python
class Settings(BaseSettings):
    # App
    APP_NAME: str = "CleanPlates"
    DEBUG: bool = False
    SECRET_KEY: str          # JWT signing key
    
    # Database
    DATABASE_URL: str        # sqlite+aiosqlite:///./cleanplates.db
    
    # Redis
    REDIS_URL: str           # redis://localhost:6379
    
    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    
    # Email
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    REPORTS_DIR: str = "./reports"
    BACKUPS_DIR: str = "./backups"
    
    # Data Retention
    AUDIT_RETENTION_DAYS: int = 90
    LOG_RETENTION_DAYS: int = 30
    
    class Config:
        env_file = ".env"
```
