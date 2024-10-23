from datetime import datetime
from functools import cached_property
from hashlib import sha256
from typing import Any, ClassVar, TypeVar

from kink import di, inject
from pydantic import BaseModel as PydanticModel
from pydantic import field_serializer
from sqlalchemy import DateTime, Engine, select
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Field, Session, SQLModel, func

T = TypeVar("T", bound="BaseModel")


class BaseModel(SQLModel):
    """A Base class for SQLModel.

    Extends the SQLModel class with additional methods.
    """

    HASH_SEPARATOR: ClassVar[str] = "-"
    key_hash: str | None = Field(default=None, primary_key=True)
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
    def business_keys(cls) -> list[str]:
        """A model must define it's business keys using this property.

        A model MUST NOT set the fields as primary key, because the
        key_hash is used as primary key.
        """  # noqa: D401
        msg = f"Must define primary keys for {cls.__name__}"
        raise NotImplementedError(msg)

    @classmethod
    def generated_keys(cls) -> list[str]:
        return sorted(["key_hash", "attribute_hash", "created_at", "updated_at"])

    @classmethod
    def attribute_keys(cls) -> set[str]:
        return set(cls.keys()) - set(cls.business_keys()) - set(cls.generated_keys())

    @cached_property
    def business_key_values(self) -> list[str]:
        """Get the primary key values of the entity."""
        return [str(getattr(self, key)) for key in sorted(self.business_keys())]

    @property
    def attribute_values(self) -> list[str]:
        """Get the attribute values of the entity."""
        return [str(getattr(self, key)) for key in sorted(self.attribute_keys())]

    @field_serializer("key_hash")
    def _key_hash_serializer(self, existing_key_hash: str | None) -> str:
        computed_key_hash = self.compute_key_hash(self)
        if existing_key_hash not in (None, computed_key_hash):
            msg = f"Key hash mismatch: existing: {existing_key_hash}, computed: {computed_key_hash}"  # noqa: E501
            raise ValueError(msg)
        return computed_key_hash

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

    @field_serializer("attribute_hash")
    def _attribute_hash_serializer(self, _: str | None) -> str:
        return sha256(
            self.HASH_SEPARATOR.join(self.attribute_values).encode()
        ).hexdigest()
