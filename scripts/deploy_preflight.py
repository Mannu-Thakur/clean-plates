"""Production deployment preflight checks for Phase 10."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path


REQUIRED_FILES = [
    "Dockerfile.prod",
    "docker-compose.prod.yml",
    "entrypoint.sh",
    "nginx/nginx.conf",
    "cloudflare/config.yml",
    "deploy/systemd/cleanplates.service",
]

REQUIRED_DIRS = ["data", "uploads", "reports", "backups", "logs"]


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        raise FileNotFoundError(f"Environment file not found: {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def parse_json_list(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) and all(isinstance(item, str) for item in value) else []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--create-dirs", action="store_true")
    args = parser.parse_args()

    ok = True
    for file_name in REQUIRED_FILES:
        if Path(file_name).exists():
            print(f"[PASS] Found {file_name}")
        else:
            print(f"[FAIL] Missing {file_name}")
            ok = False

    if args.create_dirs:
        for dir_name in REQUIRED_DIRS:
            Path(dir_name).mkdir(parents=True, exist_ok=True)

    for dir_name in REQUIRED_DIRS:
        path = Path(dir_name)
        if path.exists() and path.is_dir():
            print(f"[PASS] Directory ready: {dir_name}")
        else:
            print(f"[FAIL] Missing writable directory: {dir_name}")
            ok = False

    try:
        env = load_env(args.env_file)
    except FileNotFoundError as exc:
        print(f"[FAIL] {exc}")
        return 1

    secret = env.get("SECRET_KEY", "")
    if len(secret) >= 32 and "change-me" not in secret and "replace-with" not in secret:
        print("[PASS] SECRET_KEY is set")
    else:
        suggested = secrets.token_hex(32)
        print("[FAIL] SECRET_KEY must be a unique random value of at least 32 characters")
        print(f"       Example: SECRET_KEY={suggested}")
        ok = False

    if env.get("DEBUG", "").lower() == "false":
        print("[PASS] DEBUG=false")
    else:
        print("[FAIL] DEBUG must be false in production")
        ok = False

    if env.get("DATABASE_URL") == "sqlite+aiosqlite:///./data/cleanplates.db":
        print("[PASS] DATABASE_URL uses the shared /app/data SQLite file")
    else:
        print("[FAIL] DATABASE_URL should be sqlite+aiosqlite:///./data/cleanplates.db for this prod compose")
        ok = False

    if env.get("REDIS_URL") == "redis://redis:6379":
        print("[PASS] REDIS_URL points at the Compose Redis service")
    else:
        print("[FAIL] REDIS_URL should be redis://redis:6379 in production compose")
        ok = False

    allowed_hosts = parse_json_list(env.get("ALLOWED_HOSTS", "[]"))
    if allowed_hosts and "*" not in allowed_hosts:
        print("[PASS] ALLOWED_HOSTS is explicit")
    else:
        print("[FAIL] ALLOWED_HOSTS must be an explicit JSON list without '*'")
        ok = False

    cors_origins = parse_json_list(env.get("CORS_ORIGINS", "[]"))
    if cors_origins and "*" not in cors_origins:
        print("[PASS] CORS_ORIGINS is explicit")
    else:
        print("[FAIL] CORS_ORIGINS must be an explicit JSON list without '*'")
        ok = False

    cloudflare_config = Path("cloudflare/config.yml").read_text(encoding="utf-8")
    if "cleanplates.example.com" in cloudflare_config:
        print("[WARN] cloudflare/config.yml still contains cleanplates.example.com placeholder")
    else:
        print("[PASS] Cloudflare hostname placeholder replaced")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
