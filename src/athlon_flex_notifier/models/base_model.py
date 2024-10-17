from datetime import datetime
from functools import cached_property
from typing import TypeVar

from kink import di, inject
from sqlalchemy import Engine, select
from sqlmodel import Field, Session, SQLModel

from athlon_flex_notifier.utils import now

T = TypeVar("T", bound="BaseModel")


class BaseModel(SQLModel):
    """A Base class for SQLModel.

    Extends the SQLModel class with additional methods.
    """

    created_at: datetime | None = Field(default=now(), nullable=False, exclude=True)
    updated_at: datetime | None = Field(default_factory=now, nullable=False)

    @staticmethod
    def upsert(*entities: T) -> list[T]:
        """Upsert multiple entities into the database."""
        with Session(di["database"], expire_on_commit=False) as session:
            merged_entities = [session.merge(entity) for entity in entities]
            session.commit()
        return merged_entities

    @classmethod
    @inject
    def all(cls: T, database: Engine) -> list[T]:
        """Load all entities from the database."""
        with Session(database) as session:
            return [item[0] for item in session.exec(select(cls)).unique().all()]

    @cached_property
    def primary_keys(self) -> list[str]:
        """Get the primary keys of the entity."""
        return [key.key for key in self.__table__.primary_key.columns]

    @cached_property
    def primary_key_values(self) -> list[str]:
        """Get the primary key values of the entity."""
        return [str(getattr(self, key)) for key in self.primary_keys]
