"""Bootstrap the application, mainly setting up DI."""

import logging
import os
import smtplib
from logging import Logger

from athlon_flex_client import AthlonFlexClient
from dotenv import find_dotenv, load_dotenv
from kink import di
from prefect.exceptions import MissingContextError
from prefect.logging import get_logger, get_run_logger
from sqlalchemy import create_engine, event
from sqlalchemy.orm import with_loader_criteria
from sqlalchemy.orm.session import ORMExecuteState
from sqlmodel import Session

from athlon_flex_notifier.models.tables.base_table import BaseTable


def load_env() -> None:
    """Load environment variables from .env file."""
    load_dotenv(find_dotenv())


def bootstrap_di() -> None:
    """Setup all dependencies."""  # noqa: D401
    di[AthlonFlexClient] = lambda _: AthlonFlexClient(
        email=os.getenv("ATHLON_USERNAME", None),
        password=os.getenv("ATHLON_PASSWORD", None),
        gross_yearly_income=os.getenv("GROSS_YEARLY_INCOME", None),
        apply_loonheffingskorting=os.getenv("APPLY_LOONHEFFINGSKORTING", "true")
        == "true",
    )
    _setup_database()
    di[smtplib.SMTP] = lambda _: _smpt_server()
    # Use factory, to retry getting the prefect logger each time
    di.factories[Logger] = lambda _: _get_logger(__name__)


def database_url() -> str:
    """Get the database URL."""
    return "postgresql://{username}:{password}@{host}:{port}/{database}".format(
        username=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        database=os.getenv("POSTGRES_DB"),
    )


def _setup_database() -> None:
    """Setup database connection."""  # noqa: D401
    di["database"] = create_engine(database_url())


@event.listens_for(Session, "do_orm_execute")
def _exclude_inactive(execute_state: ORMExecuteState) -> None:
    include_inactive = execute_state.execution_options.get("include_inactive", False)
    if execute_state.is_select and not include_inactive:
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                BaseTable,
                lambda cls: (not hasattr(cls, "active_to")) or cls.active_to.is_(None),
                include_aliases=True,
            )
        )


def _get_logger(name: str) -> logging.Logger:
    """Get the logger.

    If we can get the prefect logger (we are running in a prefect flow), use it
    If not, create a new logger.
    """
    try:
        logger = get_run_logger()
    except MissingContextError:
        logger = get_logger(name)
        logger.warning("Bad prefect logger;")
    logger.setLevel(logging.DEBUG)

    return logger


def _smpt_server() -> smtplib.SMTP:
    """Configure SMTP server."""
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.ehlo()
    server.login(os.environ["EMAIL_FROM"], os.environ["GOOGLE_APP_PASSWORD"])
    return server
