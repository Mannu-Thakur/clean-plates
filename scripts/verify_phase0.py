"""Phase 0 verification tests — run with server at 127.0.0.1:8000."""
import asyncio
import sqlite3

import httpx

base = "http://127.0.0.1:8000"

# ── 1. Health check ──────────────────────────────────────────────────────────
r = httpx.get(f"{base}/health")
assert r.status_code == 200, f"Health failed: {r.text}"
print(f"[PASS] HEALTH   {r.status_code} -> {r.json()}")

# ── 2. Login with valid credentials ─────────────────────────────────────────
r = httpx.post(f"{base}/api/v1/auth/login",
               json={"email": "admin@cleanplates.dev", "password": "Admin@123"})
assert r.status_code == 200, f"Login failed: {r.text}"
data    = r.json()
access  = data["tokens"]["access_token"]
refresh = data["tokens"]["refresh_token"]
user    = data["user"]
assert user["role"] == "super_admin"
assert data["tokens"]["expires_in"] == 3600
print(f"[PASS] LOGIN    {r.status_code}  user={user['email']} role={user['role']}")

# ── 3. GET /me ───────────────────────────────────────────────────────────────
r = httpx.get(f"{base}/api/v1/auth/me",
              headers={"Authorization": f"Bearer {access}"})
assert r.status_code == 200, f"GET /me failed: {r.text}"
print(f"[PASS] GET /me  {r.status_code}")

# ── 4. Refresh token ─────────────────────────────────────────────────────────
r = httpx.post(f"{base}/api/v1/auth/refresh", json={"refresh_token": refresh})
assert r.status_code == 200, f"Refresh failed {r.status_code}: {r.text}"
new_access = r.json()["access_token"]
print(f"[PASS] REFRESH  {r.status_code}  new_token={new_access[:20]}...")

# ── 5. Logout ────────────────────────────────────────────────────────────────
r = httpx.post(f"{base}/api/v1/auth/logout",
               json={"refresh_token": refresh},
               headers={"Authorization": f"Bearer {access}"})
assert r.status_code == 200, f"Logout failed: {r.text}"
print(f"[PASS] LOGOUT   {r.status_code}")

# ── 6. Bad password → 400 ───────────────────────────────────────────────────
r = httpx.post(f"{base}/api/v1/auth/login",
               json={"email": "admin@cleanplates.dev", "password": "wrongpass"})
assert r.status_code == 400, f"Expected 400, got {r.status_code}"
print(f"[PASS] BAD PW   {r.status_code} -> {r.json()['detail']}")

# ── 7. Forgot password ────────────────────────────────────────────────────────
r = httpx.post(f"{base}/api/v1/auth/forgot-password",
               json={"email": "admin@cleanplates.dev"})
assert r.status_code == 200, f"Forgot-password failed: {r.text}"
print(f"[PASS] FORGOT   {r.status_code}")

# ── 8. No auth → 401 ─────────────────────────────────────────────────────────
r = httpx.get(f"{base}/api/v1/auth/me")
assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"
print(f"[PASS] NO AUTH  {r.status_code}")

# ── 9. SQLite WAL mode (file-level, persists) ────────────────────────────────
# Note: PRAGMA foreign_keys is connection-scoped (not stored in the file).
# We verify WAL from the file header and trust the SQLAlchemy event listener
# sets FK=ON on every connection (verified by reviewing database.py).
conn = sqlite3.connect("data/cleanplates.db")
jm = conn.execute("PRAGMA journal_mode").fetchone()[0]
conn.close()
assert jm == "wal", f"Expected WAL, got {jm}"
print(f"[PASS] PRAGMA   journal_mode={jm} (FK enforced via SQLAlchemy event listener)")

print()
print("=" * 56)
print("ALL Phase 0 verification checks PASSED")
print("=" * 56)
