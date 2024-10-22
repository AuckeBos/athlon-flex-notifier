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

    # Default hash value is not None, because then model_dump would exlude it
    DEFAULT_HASH_VALUE: ClassVar[str] = "XXX"
    HASH_SEPARATOR: ClassVar[str] = "-"
    key_hash: str | None = Field(default=DEFAULT_HASH_VALUE)
    attribute_hash: str | None = Field(default=DEFAULT_HASH_VALUE)

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
                index_elements=[*cls.primary_keys()],
                set_={
                    col: getattr(stmt.excluded, col)
                    for col in {*cls.attribute_keys(), "updated_at", "attribute_hash"}
                },
                where=cls.attribute_hash != stmt.excluded.attribute_hash,
            )
            session.exec(stmt)
            session.commit()
        # Reload from DB, to ensure all attributes are up-to-date
        result = cls.get(key_hashes=[row["key_hash"] for row in data])
        if len(result) != len(entities):
            msg = f"Upserted {len(result)} entities, expected {len(entities)}"
            raise RuntimeError(msg)
        return result

    @classmethod
    @inject
    def get(cls: T, database: Engine, *, key_hashes: list[str]) -> list[T]:
        """Load entity by list of key hashes."""
        with Session(database) as session:
            return [
                item[0]
                for item in session.exec(
                    select(cls).where(cls.key_hash.in_(key_hashes))
                ).unique()
            ]

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
    def compute_key_hash(self, existing_key_hash: str | None) -> str:
        computed_key_hash = sha256(
            self.HASH_SEPARATOR.join(self.primary_key_values).encode()
        ).hexdigest()
        if existing_key_hash not in (self.DEFAULT_HASH_VALUE, computed_key_hash):
            msg = f"Key hash mismatch: existing: {existing_key_hash}, computed: {computed_key_hash}"  # noqa: E501
            raise ValueError(msg)
        return computed_key_hash

    @field_serializer("attribute_hash")
    def compute_attribute_hash(self, _: str | None) -> str:
        return sha256(
            self.HASH_SEPARATOR.join(self.attribute_values).encode()
        ).hexdigest()
