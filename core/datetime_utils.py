"""Utility functions for handling MS SQL Server datetime quirks.

SQL Server DATETIME2 columns can return strings with up to 7 fractional-second
digits (100-nanosecond precision), e.g. '2026-02-18 04:02:12.2285367 +00:00'.
Python's ``datetime`` only supports up to 6 digits (microseconds), so we
truncate the extra digit before calling ``fromisoformat``.

All returned datetimes are timezone-aware (UTC).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

_FRACTION_RE = re.compile(r"(\.\d{6})\d+")


def parse_mssql_datetime(value: datetime | str | None) -> datetime | None:
    """Parse a datetime value that may arrive as a string from SQL Server.

    Handles:
    - ``None``  → ``None``
    - ``datetime`` (already parsed by SQLAlchemy) → normalised to UTC
    - ``str`` with 6 or 7 fractional-second digits → truncated and parsed
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        fixed = _FRACTION_RE.sub(r"\1", value)
        dt = datetime.fromisoformat(fixed)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    raise ValueError(f"Cannot parse datetime from {type(value)}: {value!r}")
