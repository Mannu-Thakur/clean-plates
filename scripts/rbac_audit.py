"""Audit route RBAC coverage and optionally probe a running server.

Static audit imports the FastAPI app and extracts role closures created by
``require_roles``. Optional HTTP probing checks that real tokens are accepted or
rejected consistently for the credentials you provide.

Examples:
    python scripts/rbac_audit.py
    python scripts/rbac_audit.py --base-url http://127.0.0.1:8000 \
      --credential super_admin=admin@cleanplates.dev:Admin@123
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import os
import re
import sys
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi.routing import APIRoute


ALL_ROLES = {
    "super_admin",
    "institution_admin",
    "mess_admin",
    "analytics_viewer",
    "staff_operator",
}

PUBLIC_PREFIXES = {
    "/health",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
}

API_KEY_PREFIXES = {
    "/api/v1/ml/",
}

PATH_PARAM_RE = re.compile(r"\{([^}:]+)(?::[^}]+)?\}")


@dataclass(frozen=True)
class RouteAudit:
    method: str
    path: str
    roles: set[str] | None
    public: bool = False
    api_key: bool = False


def extract_roles_from_dependant(dependant: Any) -> set[str]:
    roles: set[str] = set()
    for dependency in getattr(dependant, "dependencies", []):
        call = getattr(dependency, "call", None)
        if callable(call):
            try:
                closure = inspect.getclosurevars(call)
            except TypeError:
                closure = inspect.ClosureVars(nonlocals={}, globals={}, builtins={}, unbound=set())
            dependency_roles = closure.nonlocals.get("roles")
            if isinstance(dependency_roles, tuple):
                roles.update(str(role) for role in dependency_roles)
                continue
            if getattr(call, "__name__", "") in {"get_current_user", "get_current_ws_user"}:
                roles.update(ALL_ROLES)
        roles.update(extract_roles_from_dependant(dependency))
    return roles


def load_route_audits() -> list[RouteAudit]:
    os.environ.setdefault("SECRET_KEY", "rbac-audit-local-only")
    from app.main import app

    audits: list[RouteAudit] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in sorted(route.methods or []):
            if method in {"HEAD", "OPTIONS"}:
                continue
            path = route.path
            public = path in PUBLIC_PREFIXES
            api_key = any(path.startswith(prefix) for prefix in API_KEY_PREFIXES)
            roles = extract_roles_from_dependant(route.dependant)
            audits.append(
                RouteAudit(
                    method=method,
                    path=path,
                    roles=roles or None,
                    public=public,
                    api_key=api_key,
                )
            )
    return sorted(audits, key=lambda item: (item.path, item.method))


def static_audit(audits: list[RouteAudit]) -> bool:
    ok = True
    print("Static RBAC matrix")
    for audit in audits:
        if audit.public:
            access = "public"
        elif audit.api_key:
            access = "api-key"
        elif audit.roles:
            access = ",".join(sorted(audit.roles))
        else:
            access = "UNPROTECTED"
            ok = False
        print(f"{audit.method:6} {audit.path:48} {access}")
    if ok:
        print("[PASS] Every non-public HTTP route has role or API-key protection.")
    else:
        print("[FAIL] At least one non-public HTTP route lacks RBAC/API-key protection.")
    return ok


def parse_credentials(values: list[str]) -> dict[str, tuple[str, str]]:
    parsed: dict[str, tuple[str, str]] = {}
    for value in values:
        role, _, credential = value.partition("=")
        email, _, password = credential.partition(":")
        if role not in ALL_ROLES or not email or not password:
            raise ValueError(f"Invalid credential format: {value}")
        parsed[role] = (email, password)
    return parsed


def probe_path(path: str) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name == "section":
            return "institution"
        return "00000000-0000-0000-0000-000000000001"

    return PATH_PARAM_RE.sub(replace, path)


async def login(client: httpx.AsyncClient, email: str, password: str) -> str:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    response.raise_for_status()
    return response.json()["tokens"]["access_token"]


async def dynamic_probe(base_url: str, audits: list[RouteAudit], credentials: dict[str, tuple[str, str]]) -> bool:
    if not credentials:
        return True

    ok = True
    async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=10.0) as client:
        tokens = {
            role: await login(client, email, password)
            for role, (email, password) in credentials.items()
        }
        for audit in audits:
            if audit.public or audit.api_key or not audit.roles:
                continue
            path = probe_path(audit.path)
            for role, token in tokens.items():
                expected_allowed = role in audit.roles
                response = await client.request(
                    audit.method,
                    path,
                    headers={"Authorization": f"Bearer {token}"},
                    json={} if audit.method in {"POST", "PUT", "PATCH"} else None,
                )
                if expected_allowed and response.status_code in {401, 403}:
                    print(f"[FAIL] {role} should access {audit.method} {audit.path}, got {response.status_code}")
                    ok = False
                elif not expected_allowed and response.status_code != 403:
                    print(f"[FAIL] {role} should be denied {audit.method} {audit.path}, got {response.status_code}")
                    ok = False
    if ok:
        print("[PASS] Dynamic RBAC probe matched the static role matrix.")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", help="Optional running API base URL for dynamic probes")
    parser.add_argument(
        "--credential",
        action="append",
        default=[],
        help="Role credential as role=email:password. Repeat for each role.",
    )
    args = parser.parse_args()

    audits = load_route_audits()
    ok = static_audit(audits)

    if args.base_url:
        try:
            credentials = parse_credentials(args.credential)
            ok = asyncio.run(dynamic_probe(args.base_url, audits, credentials)) and ok
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] Dynamic RBAC probe failed: {exc}")
            ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
