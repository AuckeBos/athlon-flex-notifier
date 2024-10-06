import os

from dotenv import find_dotenv, load_dotenv


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


def setup_dependency_injection():
    from athlon_flex_notifier.di import Container

    container = Container()
    container.init_resources()
    container.wire()
