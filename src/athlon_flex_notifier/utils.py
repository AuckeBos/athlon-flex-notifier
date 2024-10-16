"""General utility functions."""

import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from logging import Logger

from kink import inject
from pytz import timezone


def now() -> datetime:
    """Get now in Amsterdam timezone."""
    return datetime.now(tz=timezone("Europe/Amsterdam"))


@contextmanager
@inject
def time_it(name: str, logger: Logger) -> Generator:
    """Context manager to use with the 'with' statement to time a block of code."""
    start = time.time()
    yield
    elapsed = round(time.time() - start, 4)
    logger.debug("%s took %s seconds", name, elapsed)
