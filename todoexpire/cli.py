from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Sequence

from todoexpire.parser import parse_strings
from todoexpire.reporter import render_json, render_text


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todoexpire",
        description="Scan TODO comments and flag TTL items past their deadline.",
    )
    parser.add_argument("paths", nargs="+", help="files or directories to scan")
    parser.add_argument(
        "--reference",
        default="now",
        help="reference date/time or 'now' (default: now)",
    )
    parser.add_argument(
        "--warning-days",
        default=2,
        type=_positive_int,
        help="days before expiry to mark as warning",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit JSON instead of human-readable text",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    items = parse_strings(args.paths)
    from todoexpire.expiry import evaluate
    results = evaluate(items, reference=args.reference, warning_days=args.warning_days)

    if args.json:
        print(render_json(results))
    else:
        print(render_text(results))

    return 1 if any(r.status == "expired" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
