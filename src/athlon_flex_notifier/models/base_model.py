from datetime import datetime
from functools import cached_property
from hashlib import sha256
from typing import ClassVar, TypeVar

from kink import di, inject
from pydantic import field_serializer
from sqlalchemy import DateTime, Engine, inspect, select
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Field, Relationship, Session, SQLModel, func

T = TypeVar("T", bound="BaseModel")


class BaseModel(SQLModel):
    """A Base class for SQLModel.

    Extends the SQLModel class with additional methods.
    """

    HASH_SEPARATOR: ClassVar[str] = "-"

    key_hash: str | None = Field(default=None, unique=True)
    attribute_hash: str | None = Field(default=None)

    created_at: datetime | None = Field(
        exclude=True,
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()},
    )
    updated_at: datetime | None = Field(
        exclude=True,
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "onupdate": func.now(),
            "server_default": func.now(),
            "server_onupdate": func.now(),
        },
    )

    @classmethod
    def upsert(cls, *entities: T) -> list[T]:
        """Upsert multiple entities into the database."""
        if not entities:
            return []
        data = [entity.model_dump() for entity in entities]
        with Session(di["database"], expire_on_commit=False) as session:
            stmt = insert(cls).values(data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["key_hash"],
                set_={
                    col: getattr(stmt.excluded, col)
                    for col in {*cls.attribute_keys(), "updated_at", "attribute_hash"}
                },
                where=cls.attribute_hash != stmt.excluded.attribute_hash,
            )
            session.exec(stmt)
            session.commit()
        return entities

    @classmethod
    @inject
    def all(cls: T, database: Engine) -> list[T]:
        """Load all entities from the database."""
        with Session(database) as session:
            return [item[0] for item in session.exec(select(cls)).unique().all()]

    @classmethod
    def keys(cls) -> list[str]:
        """Get the keys of the entity."""
        return sorted([key.key for key in cls.__table__.c])

    @classmethod
    def primary_keys(cls) -> list[str]:
        """Get the primary keys of the entity."""
        return sorted([key.key for key in cls.__table__.primary_key.columns])

    @classmethod
    def generated_keys(cls) -> list[str]:
        return sorted(["key_hash", "attribute_hash", "created_at", "updated_at"])

    @classmethod
    def attribute_keys(cls) -> set[str]:
        return sorted(
            set(cls.keys()) - set(cls.primary_keys()) - set(cls.generated_keys())
        )

    @cached_property
    def primary_key_values(self) -> list[str]:
        """Get the primary key values of the entity."""
        return [str(getattr(self, key)) for key in self.primary_keys()]

    @property
    def attribute_values(self) -> list[str]:
        """Get the attribute values of the entity."""
        return [str(getattr(self, key)) for key in self.attribute_keys()]

    @cached_property
    def relationships(self) -> list[Relationship]:
        """Get the relationships of the entity."""
        return inspect(self).mapper.relationships.values()

    @field_serializer("key_hash")
    def compute_key_hash(self, key_hash: str | None) -> str:
        return sha256(
            self.HASH_SEPARATOR.join(self.primary_key_values).encode()
        ).hexdigest()

    @field_serializer("attribute_hash")
    def compute_attribute_hash(self, attribute_hash: str | None) -> str:
        return sha256(
            self.HASH_SEPARATOR.join(self.attribute_values).encode()
        ).hexdigest()
