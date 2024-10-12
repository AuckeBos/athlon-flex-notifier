"""General utility functions."""

from datetime import datetime

from pytz import timezone


def now() -> datetime:
    """Get now in Amsterdam timezone."""
    return datetime.now(tz=timezone("Europe/Amsterdam"))
