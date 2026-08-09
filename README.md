# todoexpire

<p align="left">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python" />
  <img src="https://img.shields.io/badge/status-stable-green" alt="Status" />
  <img src="https://img.shields.io/badge/cli-todo-green" alt="CLI" />
</p>

Identify TODO comments that have outlived their TTL.

## About

`todoexpire` scans source files for TODO-style comments and flags items whose
time-to-live threshold has passed relative to an inspected reference date or
the current local time. It is designed for small audits and CI checks where
stale action items need to be surfaced without manual review.

It intentionally assumes inline references over external tracking systems so
the command stays deterministic and reproducible.

## Features

- Parse TODO comments with optional TTL tokens such as `ttl:24h`, `ttl:7d`,
  `ttl:2w`, or `ttl:2026-08-01`.
- Flag items whose TTL expired before a reference timestamp.
- Report counts by `expired`, `warning`, and `healthy` status.
- Run inline audit from the CLI with sensible defaults.
- Works across multiple files and supports standard comment styles.
- Pure stdlib implementation.

## Installation

```bash
python -m pip install -e .
```

## Usage

```bash
todoexpire audit ./src --reference "2026-08-01"
todoexpire audit ./src --reference now
todoexpire audit app.py tests/ --json
todoexpire audit package/ --skip-test
```

## Supported TTL formats

- `ttl:24h` — hours
- `ttl:7d` — days
- `ttl:2w` — weeks
- `ttl:2026-08-01` — fixed calendar date

## Project structure

```
todoexpire/
  pyproject.toml
  todoexpire/
    __init__.py
    parser.py
    expiry.py
    reporter.py
    cli.py
  README.md
```

## Tags / keywords

cli, todo, ttl, audit, python
