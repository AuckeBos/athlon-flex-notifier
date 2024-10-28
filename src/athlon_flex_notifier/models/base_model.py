from datetime import datetime
from functools import cached_property
from hashlib import sha256
from typing import Any, ClassVar, TypeVar

from kink import inject
from pydantic import BaseModel as PydanticModel
from pydantic import field_serializer
from sqlalchemy import DateTime, Engine, select
from sqlmodel import Field, Session, SQLModel, func

from athlon_flex_notifier.upserter import Upserter

T = TypeVar("T", bound="BaseModel")


class BaseModel(SQLModel):
    """A Base class for SQLModel.

    Extends the SQLModel class with additional methods.

    - key_hash is a computed sha256 hash of the business keys
    - attribute_hash is a computed sha256 hash of the attribute values
    - id is the technical key, and a sha256 of the key_hash and attribute_hash
    """

    HASH_SEPARATOR: ClassVar[str] = "-"
    id: str | None = Field(default=None, primary_key=True)
    key_hash: str | None = Field(default=None)
    attribute_hash: str | None = Field(default=None)

    active_from: datetime | None = Field(
        nullable=False, sa_type=DateTime(timezone=True)
    )
    active_to: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    deleted_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))

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
        return Upserter(entities=entities).scd2()

    @classmethod
    @inject
    def get(cls: T, database: Engine, *, key_hashes: list[str]) -> list[T]:
        """Load entity by list of ids."""
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
    def business_keys(cls) -> list[str]:
        """A model must define it's business keys using this property.

        A model MUST NOT set the fields as primary key, because the
        id is used as primary key.
        """  # noqa: D401
        msg = f"Must define primary keys for {cls.__name__}"
        raise NotImplementedError(msg)

    @classmethod
    def generated_keys(cls) -> list[str]:
        return sorted(
            [
                "id",
                "key_hash",
                "attribute_hash",
                "created_at",
                "updated_at",
                "active_from",
                "active_to",
                "deleted_at",
            ]
        )

    @classmethod
    def attribute_keys(cls) -> set[str]:
        return set(cls.keys()) - set(cls.business_keys()) - set(
            cls.generated_keys()
        ) | {"deleted_at"}

    @cached_property
    def business_key_values(self) -> list[str]:
        """Get the primary key values of the entity."""
        return [str(getattr(self, key)) for key in sorted(self.business_keys())]

    @property
    def attribute_values(self) -> list[str]:
        """Get the attribute values of the entity."""
        return [str(getattr(self, key)) for key in sorted(self.attribute_keys())]

    @classmethod
    def compute_key_hash(cls, entity: PydanticModel | dict[str, Any]) -> str:
        """Publically available class method to compute the key hash for an entity.

        Parameters
        ----------
        entity : PydanticModel | dict[str, Any]
            Entity to compute hash for. Can be a Pydantic model
            (a base model or sqlmodel), or a dict (the dump).

        Returns
        -------
        str sha256 hash

        """
        if isinstance(entity, PydanticModel):
            values = [str(getattr(entity, key)) for key in cls.business_keys()]
        else:
            values = [str(entity[key]) for key in cls.business_keys()]
        return sha256(cls.HASH_SEPARATOR.join(values).encode()).hexdigest()

    @classmethod
    def _compute_attribute_hash(cls, entity: PydanticModel | dict[str, Any]) -> str:
        if isinstance(entity, PydanticModel):
            values = [str(getattr(entity, key)) for key in cls.attribute_keys()]
        else:
            values = [str(entity[key]) for key in cls.attribute_keys()]
        return sha256(cls.HASH_SEPARATOR.join(values).encode()).hexdigest()

    @classmethod
    def compute_id(cls, entity: PydanticModel | dict[str, Any]) -> str:
        values = [cls.compute_key_hash(entity), cls._compute_attribute_hash(entity)]
        return sha256(cls.HASH_SEPARATOR.join(values).encode()).hexdigest()

    @field_serializer("attribute_hash")
    def _attribute_hash_serializer(self, _: str | None) -> str:
        return self._compute_attribute_hash(self)

    @field_serializer("key_hash")
    def _key_hash_serializer(self, _: str | None) -> str:
        return self.compute_key_hash(self)

    @field_serializer("id")
    def _id(self, _: str | None) -> str:
        return self.compute_id(self)
