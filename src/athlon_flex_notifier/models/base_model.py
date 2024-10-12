from functools import cached_property, reduce
from typing import Optional, TypeVar

from kink import inject
from sqlalchemy import Engine, select
from sqlmodel import Session, SQLModel

T = TypeVar("T", bound="BaseModel")


class BaseModel(SQLModel):
    @cached_property
    def _primary_keys(self) -> list[str]:
        """Find the primary keys, based on field properties"""
        return [
            name
            for name, field in self.__fields__.items()
            if getattr(field, "primary_key", False) == True  # noqa: E712
        ]

    @cached_property
    def _business_keys(self) -> list[str] | None:
        """If differs from primary keys, must be implemented by subclasses"""
        return None

    def _get_existing_model_based_on_business_keys(
        self: T, session: Session
    ) -> Optional["T"]:
        """Find existing model based on business keys, if any"""
        keys = self._business_keys or self._primary_keys
        query = reduce(
            lambda query, key: query.where(
                getattr(self, key) == getattr(self.__class__, key)
            ),
            keys,
            select(self.__class__),
        )
        if result := session.exec(query).first():
            return result[0]
        return None

    @inject
    def upsert(self: T, database: Engine) -> T:
        model = self
        with Session(database, expire_on_commit=False) as session:
            if existing_model := self._get_existing_model_based_on_business_keys(
                session
            ):
                model = existing_model.sqlmodel_update(self)
            session.add(model)
            session.commit()
        return model
