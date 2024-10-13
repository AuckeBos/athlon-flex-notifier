"""Bootstrap the application, mainly setting up DI."""

import logging
import os
import smtplib
from logging import Logger

from athlon_flex_api import AthlonFlexApi
from dotenv import find_dotenv, load_dotenv
from kink import di
from sqlalchemy import create_engine
from sqlmodel import SQLModel

from athlon_flex_notifier.notifications.console_notifier import ConsoleNotifier
from athlon_flex_notifier.notifications.email_notifier import EmailNotifier
from athlon_flex_notifier.notifications.notifiers import Notifiers


def load_env() -> None:
    """Load environment variables from .env file."""
    load_dotenv(find_dotenv())


def bootstrap_di() -> None:
    """Setup all dependencies."""  # noqa: D401
    di[AthlonFlexApi] = AthlonFlexApi(
        email=os.getenv("ATHLON_USERNAME", None),
        password=os.getenv("ATHLON_PASSWORD", None),
        gross_yearly_income=os.getenv("GROSS_YEARLY_INCOME", None),
        apply_loonheffingskorting=os.getenv("APPLY_LOONHEFFINGSKORTING", "true")
        == "true",
    )
    _setup_database()
    _setup_logger()
    di[smtplib.SMTP] = lambda di_: _smpt_server()
    di[Notifiers] = lambda di_: Notifiers(
        notifiers=[ConsoleNotifier(), EmailNotifier(di_)]
    )


def _setup_database():
    """Setup database connection."""  # noqa: D401
    di["database"] = create_engine(
        "postgresql://{username}:{password}@{host}:{port}/{database}".format(
            username=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            database=os.getenv("POSTGRES_DB"),
        )
    )
    import athlon_flex_notifier.models  # noqa: F401

    SQLModel.metadata.create_all(di["database"])


def _setup_logger() -> Logger:
    """Configure logger."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    log_format = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    di[Logger] = logger


def _smpt_server() -> smtplib.SMTP:
    """Configure SMTP server."""
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.ehlo()
    server.login(os.environ["EMAIL_FROM"], os.environ["GOOGLE_APP_PASSWORD"])
    return server
