from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional

_COMMENT_RE = re.compile(r"#\s*(?P<token>TODO|FIXME)\b", flags=re.IGNORECASE)


@dataclass(frozen=True)
class TodoItem:
    path: str
    line_number: int
    raw: str
    token: str
    ttl_text: Optional[str] = None


def _iter_lines(path: Path) -> Iterable[tuple[int, str, str]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    for idx, line in enumerate(text.splitlines(), start=1):
        yield idx, line, text


def parse_strings(paths: Iterable[str | Path]) -> List[TodoItem]:
    items: List[TodoItem] = []
    seen: set[tuple[str, int]] = set()
    for raw_path in paths:
        p = Path(raw_path)
        if p.is_dir():
            candidates = sorted(p.rglob("*"))
        else:
            candidates = [p]
        for path in candidates:
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".py", ".md", ".txt", ".toml", ".yaml", ".yml", ".sh"}:
                continue
            for line_number, line, _ in _iter_lines(path):
                match = _COMMENT_RE.search(line)
                if not match:
                    continue
                token = match.group("token").upper()
                ttl_text = _extract_ttl(line)
                key = (str(path), line_number)
                if key in seen:
                    continue
                seen.add(key)
                items.append(
                    TodoItem(
                        path=str(path),
                        line_number=line_number,
                        raw=line.strip(),
                        token=token,
                        ttl_text=ttl_text,
                    )
                )
    return items


def _extract_ttl(text: str) -> Optional[str]:
    match = re.search(r"ttl\s*:\s*([^\s]+)", text, flags=re.IGNORECASE)
    return match.group(1) if match else None
