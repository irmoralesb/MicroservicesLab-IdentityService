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
            # Treat naive datetimes as UTC
            return value.replace(tzinfo=timezone.utc)
        # Normalise any offset-aware datetime to UTC
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        # Truncate extra fractional digits beyond microseconds
        fixed = _FRACTION_RE.sub(r"\1", value)
        # Normalise optional space before the UTC offset, e.g. '...228536 +00:00' → '...228536+00:00'
        fixed = re.sub(r"(\d)\s+([+-]\d{2}:\d{2})$", r"\1\2", fixed)
        dt = datetime.fromisoformat(fixed)
        if dt.tzinfo is None:
            # Treat naive datetimes as UTC
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            # Normalise any offset-aware datetime to UTC
            dt = dt.astimezone(timezone.utc)
        return dt
    raise ValueError(f"Cannot parse datetime from {type(value)}: {value!r}")
