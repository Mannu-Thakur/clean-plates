"""PDF report generation helpers.

WeasyPrint is used when available. A small built-in PDF fallback keeps local
tests and minimal deployments functional when the native Cairo/Pango stack is
not installed yet.
"""

from __future__ import annotations

import asyncio
import html
from typing import Any


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _minimal_pdf_bytes(title: str, lines: list[str]) -> bytes:
    content_lines = ["BT", "/F1 12 Tf", "72 760 Td", "16 TL", f"({_pdf_escape(title)}) Tj"]
    for line in lines[:42]:
        content_lines.append("T*")
        content_lines.append(f"({_pdf_escape(line[:100])}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{idx} 0 obj\n".encode())
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref_start = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode()
    )
    return bytes(output)


def _html_document(title: str, summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    summary_items = "".join(
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(value))}</td></tr>"
        for key, value in summary.items()
    )
    headers = list(rows[0].keys()) if rows else []
    header_html = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
    row_html = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(row.get(header, '')))}</td>" for header in headers) + "</tr>"
        for row in rows[:200]
    )
    return f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          body {{ font-family: Inter, Arial, sans-serif; color: #111827; margin: 36px; }}
          h1 {{ font-size: 24px; margin-bottom: 8px; }}
          table {{ border-collapse: collapse; width: 100%; margin-top: 18px; }}
          th, td {{ border: 1px solid #d1d5db; padding: 7px 9px; font-size: 11px; text-align: left; }}
          th {{ background: #f3f4f6; }}
        </style>
      </head>
      <body>
        <h1>{html.escape(title)}</h1>
        <table>{summary_items}</table>
        <table><thead><tr>{header_html}</tr></thead><tbody>{row_html}</tbody></table>
      </body>
    </html>
    """


def _build_pdf_sync(title: str, summary: dict[str, Any], rows: list[dict[str, Any]]) -> bytes:
    document = _html_document(title, summary, rows)
    try:
        from weasyprint import HTML
    except Exception:
        lines = [f"{key}: {value}" for key, value in summary.items()]
        for row in rows[:30]:
            lines.append(" | ".join(f"{key}: {value}" for key, value in row.items()))
        return _minimal_pdf_bytes(title, lines)
    return HTML(string=document).write_pdf()


def _write_file(path: str, content: bytes) -> int:
    with open(path, "wb") as handle:
        handle.write(content)
    return len(content)

async def write_pdf(path: str, title: str, summary: dict[str, Any], rows: list[dict[str, Any]]) -> int:
    content = await asyncio.to_thread(_build_pdf_sync, title, summary, rows)
    return await asyncio.to_thread(_write_file, path, content)
