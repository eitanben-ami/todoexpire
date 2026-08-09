from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from todoexpire.parser import TodoItem

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PARSE_UNIT_RE = re.compile(r"^(?P<value>\d+)(?P<unit>h|d|w)$")
_DEFAULT_WARNING_DAYS = 2


class ParseError(Exception):
    pass


@dataclass(frozen=True)
class ExpiryResult:
    item: TodoItem
    expires_at: Optional[datetime]
    status: str  # healthy, warning, expired
    ttl_text: Optional[str]


def _parse_ttl(ttl_text: str, reference: datetime) -> datetime:
    if _DATE_RE.match(ttl_text):
        try:
            return datetime.strptime(ttl_text, "%Y-%m-%d").replace(tzinfo=reference.tzinfo)
        except ValueError as exc:
            raise ParseError(f"invalid date: {ttl_text}") from exc

    match = _PARSE_UNIT_RE.match(ttl_text)
    if not match:
        raise ParseError(f"unsupported TTL format: {ttl_text}")
    value = int(match.group("value"))
    unit = match.group("unit")
    delta = timedelta()
    if unit == "h":
        delta = timedelta(hours=value)
    elif unit == "d":
        delta = timedelta(days=value)
    elif unit == "w":
        delta = timedelta(weeks=value)
    return reference + delta


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def evaluate(
    items: List[TodoItem],
    reference: Optional[str] = None,
    warning_days: int = _DEFAULT_WARNING_DAYS,
) -> List[ExpiryResult]:
    if reference is None or reference.lower() == "now":
        ref = _now_utc()
    else:
        try:
            ref = datetime.fromisoformat(reference)
        except ValueError as exc:
            raise ParseError(f"unsupported reference datetime: {reference}") from exc
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)

    warning_threshold = ref + timedelta(days=warning_days)
    results: List[ExpiryResult] = []
    for item in items:
        if item.ttl_text:
            try:
                expires_at = _parse_ttl(item.ttl_text, ref)
            except ParseError:
                results.append(ExpiryResult(item=item, expires_at=None, status="healthy", ttl_text=item.ttl_text))
                continue
            if expires_at < ref:
                status = "expired"
            elif expires_at <= warning_threshold:
                status = "warning"
            else:
                status = "healthy"
        else:
            expires_at = None
            status = "healthy"
        results.append(ExpiryResult(item=item, expires_at=expires_at, status=status, ttl_text=item.ttl_text))
    return results
