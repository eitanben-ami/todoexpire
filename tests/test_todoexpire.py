from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

from todoexpire.parser import TodoItem, parse_strings
from todoexpire.expiry import evaluate
from todoexpire.reporter import render_text, render_json


@dataclass(frozen=True)
class FakeItem(TodoItem):
    pass


def test_parse_strings_detects_todos(tmp_path: Path):
    target = tmp_path / "sample.py"
    target.write_text(
        "x = 1\n"
        "def run():\n"
        "# FIXME: urgent followed by notes\n"
        "# TODO: handle wrapping ttl:24h\n"
    )
    items = parse_strings([str(target)])
    assert len(items) == 2
    tokens = [item.token.lower() for item in items]
    assert "fixme" in tokens
    assert "todo" in tokens
    line_numbers = [item.line_number for item in items]
    assert line_numbers == [3, 4]
    assert any(item.ttl_text == "24h" for item in items)


def test_parse_strings_ignores_non_selected_extensions(tmp_path: Path):
    target = tmp_path / "sample.bin"
    target.write_text("not a real file")
    parsed = parse_strings([str(target)])
    assert parsed == []


def test_evaluate_expired_with_fixed_date_reference():
    items = [FakeItem(path="app.py", line_number=1, raw="# TODO: cleanup auth ttl:2025-01-01", token="TODO", ttl_text="2025-01-01")]
    reference = datetime(2026, 1, 1, tzinfo=timezone.utc)
    results = evaluate(items, reference=reference.strftime("%Y-%m-%dT%H:%M:%SZ"))
    assert results[0].status == "expired"


def test_evaluate_warning_threshold():
    items = [FakeItem(path="app.py", line_number=1, raw="# TODO: polish docs ttl:7d", token="TODO", ttl_text="7d")]
    reference = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    results = evaluate(items, reference=reference.strftime("%Y-%m-%dT%H:%M:%SZ"), warning_days=3)
    assert results[0].status == "healthy"
    assert results[0].expires_at == reference + timedelta(days=7)


def test_evaluate_no_ttl_is_healthy():
    items = [FakeItem(path="app.py", line_number=1, raw="# TODO: general cleanup", token="TODO", ttl_text=None)]
    results = evaluate(items, reference="now")
    assert results[0].status == "healthy"


def test_render_json_contains_summary():
    items = [FakeItem(path="a.py", line_number=1, raw="# TODO: x ttl:24h", token="TODO", ttl_text="24h")]
    results = evaluate(items, reference="now")
    text = render_json(results)
    assert "summary" in text
    assert "items" in text
    assert "a.py" in text


def test_render_text_counts_groups_by_status():
    items = [
        FakeItem(path="a.py", line_number=1, raw="# TODO: a ttl:2025-01-01", token="TODO", ttl_text="2025-01-01"),
        FakeItem(path="b.py", line_number=2, raw="# TODO: b ttl:24h", token="TODO", ttl_text="24h"),
        FakeItem(path="c.py", line_number=3, raw="# TODO: c", token="TODO", ttl_text=None),
    ]
    results = evaluate(items, reference=datetime(2026, 8, 1, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    text = render_text(results)
    assert "[expired]" in text
    assert "[healthy]" in text
    assert text.startswith("TODOs: total=")


def test_evaluate_supports_week_ttl():
    items = [FakeItem(path="app.py", line_number=1, raw="# TODO: long-lived todo ttl:2w", token="TODO", ttl_text="2w")]
    reference = datetime(2026, 8, 1, tzinfo=timezone.utc)
    results = evaluate(items, reference=reference.strftime("%Y-%m-%dT%H:%M:%SZ"))
    assert results[0].status == "healthy"
    assert results[0].expires_at == reference + timedelta(weeks=2)


def test_expiry_invalid_ttl_treated_as_healthy():
    items = [FakeItem(path="app.py", line_number=1, raw="# TODO: weird todo ttl:foobar", token="TODO", ttl_text="foobar")]
    results = evaluate(items, reference="now")
    assert results[0].status == "healthy"
    assert results[0].expires_at is None


def test_parse_strings_deduplicates_same_path_and_line(tmp_path: Path):
    target = tmp_path / "sample.py"
    target.write_text("# TODO: same ttl:24h\n# TODO: same ttl:24h\n")
    items = parse_strings([str(target)])
    same_line = [item for item in items if item.path == str(target) and item.line_number == 1]
    assert len(same_line) == 1
