import os

from athlon_flex_api import AthlonFlexApi
from dotenv import find_dotenv, load_dotenv
from kink import di


def load_env():
    load_dotenv(find_dotenv())


def setup_mongo_engine():
    from mongoengine import connect

    connect(
        db=os.getenv("MONGO_DB"),
        username=os.getenv("MONGO_USER"),
        password=os.getenv("MONGO_PASSWORD"),
        host=os.getenv("MONGO_HOST", "localhost"),
        port=int(os.getenv("MONGO_PORT", "27017")),
    )


def bootstrap_di():
    di[AthlonFlexApi] = AthlonFlexApi(
        email=os.getenv("ATHLON_USERNAME", None),
        password=os.getenv("ATHLON_PASSWORD", None),
        gross_yearly_income=os.getenv("GROSS_YEARLY_INCOME", None),
        apply_loonheffingskorting=os.getenv("APPLY_LOONHEFFINGSKORTING", "true")
        == "true",
    )
