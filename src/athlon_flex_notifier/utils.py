"""General utility functions."""

import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timezone
from logging import Logger

from kink import inject


def now() -> datetime:
    """Get now in Amsterdam timezone."""
    return datetime.now(timezone.utc)


@contextmanager
@inject
def time_it(name: str, logger: Logger) -> Generator:
    """Context manager to use with the 'with' statement to time a block of code."""
    start = time.time()
    yield
    elapsed = round(time.time() - start, 4)
    logger.debug("%s took %s seconds", name, elapsed)
