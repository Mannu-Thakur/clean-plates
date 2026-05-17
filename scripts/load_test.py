"""Small production smoke/load test for CleanPlates.

The goal is not to replace k6/JMeter; it is a quick Phase 10 gate for the
documented latency targets:
  - CRUD/read endpoints p95 under 100 ms
  - analytics endpoints p95 under 500 ms

Usage:
    python scripts/load_test.py --base-url http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time
from dataclasses import dataclass

import httpx


CRUD_ENDPOINTS = [
    "/api/v1/auth/me",
    "/api/v1/students/",
    "/api/v1/waste/entries",
    "/api/v1/devices/",
    "/api/v1/reports/",
    "/api/v1/notifications/",
    "/api/v1/config/institution",
]

ANALYTICS_ENDPOINTS = [
    "/api/v1/analytics/overview",
    "/api/v1/analytics/trends",
    "/api/v1/analytics/peaks",
    "/api/v1/analytics/meal-distribution",
    "/api/v1/analytics/sustainability",
]


@dataclass
class Sample:
    endpoint: str
    group: str
    status_code: int
    elapsed_ms: float
    error: str | None = None


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(int(round((pct / 100) * (len(ordered) - 1))), len(ordered) - 1)
    return ordered[index]


async def login(client: httpx.AsyncClient, email: str, password: str) -> str:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    response.raise_for_status()
    payload = response.json()
    return payload["tokens"]["access_token"]


async def timed_get(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    endpoint: str,
    group: str,
) -> Sample:
    async with semaphore:
        start = time.perf_counter()
        try:
            response = await client.get(endpoint)
            elapsed_ms = (time.perf_counter() - start) * 1000
            error = None if response.status_code < 500 else response.text[:200]
            return Sample(endpoint, group, response.status_code, elapsed_ms, error)
        except Exception as exc:  # noqa: BLE001
            elapsed_ms = (time.perf_counter() - start) * 1000
            return Sample(endpoint, group, 0, elapsed_ms, str(exc))


def print_group(name: str, samples: list[Sample], threshold_ms: float) -> bool:
    values = [sample.elapsed_ms for sample in samples]
    failures = [sample for sample in samples if sample.status_code >= 400 or sample.status_code == 0 or sample.error]
    p50 = percentile(values, 50)
    p95 = percentile(values, 95)
    avg = statistics.fmean(values) if values else 0.0
    ok = not failures and p95 <= threshold_ms
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: count={len(samples)} avg={avg:.1f}ms p50={p50:.1f}ms p95={p95:.1f}ms")
    if failures:
        for sample in failures[:10]:
            print(f"  - {sample.endpoint} -> {sample.status_code} {sample.error or ''}".strip())
    if p95 > threshold_ms:
        print(f"  - p95 target exceeded: {p95:.1f}ms > {threshold_ms:.1f}ms")
    return ok


async def run(args: argparse.Namespace) -> int:
    timeout = httpx.Timeout(args.timeout)
    limits = httpx.Limits(max_connections=args.concurrency * 2, max_keepalive_connections=args.concurrency)
    async with httpx.AsyncClient(base_url=args.base_url.rstrip("/"), timeout=timeout, limits=limits) as client:
        health = await client.get("/health")
        health.raise_for_status()

        token = await login(client, args.email, args.password)
        client.headers.update({"Authorization": f"Bearer {token}"})

        semaphore = asyncio.Semaphore(args.concurrency)
        tasks = []
        for _ in range(args.requests):
            tasks.extend(timed_get(client, semaphore, endpoint, "CRUD",) for endpoint in CRUD_ENDPOINTS)
            tasks.extend(timed_get(client, semaphore, endpoint, "Analytics") for endpoint in ANALYTICS_ENDPOINTS)

        samples = await asyncio.gather(*tasks)

    crud_ok = print_group(
        "CRUD/read endpoints",
        [sample for sample in samples if sample.group == "CRUD"],
        args.crud_p95_ms,
    )
    analytics_ok = print_group(
        "Analytics endpoints",
        [sample for sample in samples if sample.group == "Analytics"],
        args.analytics_p95_ms,
    )
    return 0 if crud_ok and analytics_ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--email", default="admin@cleanplates.dev")
    parser.add_argument("--password", default="Admin@123")
    parser.add_argument("--requests", type=int, default=10, help="Iterations per endpoint")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--crud-p95-ms", type=float, default=100.0)
    parser.add_argument("--analytics-p95-ms", type=float, default=500.0)
    args = parser.parse_args()
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
