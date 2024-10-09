import os

from athlon_flex_api import AthlonFlexApi
from dotenv import find_dotenv, load_dotenv
from kink import di
from sqlalchemy import create_engine
from sqlmodel import SQLModel


def load_env():
    load_dotenv(find_dotenv())


def bootstrap_di():
    di[AthlonFlexApi] = AthlonFlexApi(
        email=os.getenv("ATHLON_USERNAME", None),
        password=os.getenv("ATHLON_PASSWORD", None),
        gross_yearly_income=os.getenv("GROSS_YEARLY_INCOME", None),
        apply_loonheffingskorting=os.getenv("APPLY_LOONHEFFINGSKORTING", "true")
        == "true",
    )
    setup_database()


def setup_database():
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
