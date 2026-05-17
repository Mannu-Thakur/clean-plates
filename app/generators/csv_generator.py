"""CSV report generation helpers."""

from __future__ import annotations

import csv
import io
from typing import Any


def build_csv_bytes(headers: list[str], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({header: row.get(header, "") for header in headers})
    return buffer.getvalue().encode("utf-8-sig")


async def write_csv(path: str, headers: list[str], rows: list[dict[str, Any]]) -> int:
    content = build_csv_bytes(headers, rows)
    with open(path, "wb") as handle:
        handle.write(content)
    return len(content)
