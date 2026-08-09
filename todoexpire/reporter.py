from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from todoexpire.expiry import ExpiryResult


def _format_ts(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(value)


def render_text(results: List[ExpiryResult]) -> str:
    expired = [r for r in results if r.status == "expired"]
    warning = [r for r in results if r.status == "warning"]
    healthy = [r for r in results if r.status == "healthy"]

    lines = [
        f"TODOs: total={len(results)} expired={len(expired)} warning={len(warning)} healthy={len(healthy)}"
    ]
    for label, group in [("expired", expired), ("warning", warning), ("healthy", healthy)]:
        if not group:
            continue
        lines.append(f"[{label}]")
        for result in group:
            item = result.item
            lines.append(
                f"- {item.path}:{item.line_number} {item.token} ttl={result.ttl_text or '-'} expires_at={_format_ts(result.expires_at)}"
            )
    return "\n".join(lines)


def render_json(results: List[ExpiryResult]) -> str:
    import json

    payload = []
    for result in results:
        item = result.item
        payload.append(
            {
                "path": item.path,
                "line_number": item.line_number,
                "token": item.token,
                "raw": item.raw,
                "ttl_text": item.ttl_text,
                "expires_at": _format_ts(result.expires_at),
                "status": result.status,
            }
        )
    return json.dumps(
        {
            "summary": {
                "total": len(results),
                "expired": sum(1 for r in results if r.status == "expired"),
                "warning": sum(1 for r in results if r.status == "warning"),
                "healthy": sum(1 for r in results if r.status == "healthy"),
            },
            "items": payload,
        },
        indent=2,
    )
