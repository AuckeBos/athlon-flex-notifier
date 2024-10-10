from functools import reduce
from typing import TypeVar

from kink import inject
from sqlalchemy import Engine, select
from sqlmodel import Session, SQLModel

T = TypeVar("T", bound=SQLModel)


def _primary_keys(model: T) -> list[str]:
    return [
        name
        for name, field in model.__fields__.items()
        if getattr(field, "primary_key", False) == True
    ]


# Todo: Move to ModelUpdater Service
# Todo: Document
@inject
def upsert(*, model: T, business_keys: list[str] = None, database: Engine) -> T:
    keys = business_keys or _primary_keys(model)
    with Session(database, expire_on_commit=False) as session:
        query = reduce(
            lambda query, key: query.where(
                getattr(model, key) == getattr(model.__class__, key)
            ),
            keys,
            select(model.__class__),
        )
        if existing_model := session.exec(query).first():
            model = _update_fields(existing_model[0], model)
        session.add(model)
        session.commit()
    return model


def _update_fields(existing_model: T, new_model: T) -> T:
    primary_keys = _primary_keys(new_model)
    for key, value in existing_model.model_dump().items():
        if key in primary_keys:
            continue
        setattr(existing_model, key, value)
    return existing_model
