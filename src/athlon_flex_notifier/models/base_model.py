from datetime import datetime
from functools import cached_property
from hashlib import sha256
from typing import ClassVar, TypeVar
from uuid import UUID, uuid4

from kink import inject
from pydantic import field_serializer
from sqlalchemy import UUID as SQLAlchemyUUID
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

    KNOWN ISSUES:
        - sort_order doesn't work: https://github.com/fastapi/sqlmodel/issues/542
            Kept in code, for future reference
        - alias doesn't work: https://github.com/fastapi/sqlmodel/discussions/725
            https://stackoverflow.com/questions/77819208/how-can-i-use-alias-in-sqlmodel-library
            Removed from code, to prevent unclarity
    """

    HASH_SEPARATOR: ClassVar[str] = "-"
    id: UUID = Field(
        primary_key=True,
        sa_type=SQLAlchemyUUID(as_uuid=True),
        default_factory=uuid4,
    )
    key_hash: str | None = Field(
        default=None,
        sa_column_kwargs={"sort_order": 90},
    )
    attribute_hash: str | None = Field(
        default=None,
        sa_column_kwargs={"sort_order": 91},
    )

    active_from: datetime | None = Field(
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"sort_order": 92},
    )
    active_to: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"sort_order": 93},
    )

    created_at: datetime | None = Field(
        exclude=True,
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),
            "sort_order": 94,
        },
    )
    updated_at: datetime | None = Field(
        exclude=True,
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "onupdate": func.now(),
            "server_default": func.now(),
            "server_onupdate": func.now(),
            "sort_order": 95,
        },
    )

    @classmethod
    def upsert(cls, *entities: T) -> dict[str, T]:
        """Upsert multiple entities into the database.

        Returns
        -------
        dict[str, T], maps key_hash the upserted entity

        """
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
            ]
        )

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

    @field_serializer("attribute_hash")
    def _attribute_hash_serializer(self, _: str | None) -> str:
        return sha256(
            self.HASH_SEPARATOR.join(self.attribute_values).encode()
        ).hexdigest()

    @field_serializer("key_hash")
    def _key_hash_serializer(self, _: str | None) -> str:
        return self.compute_key_hash()

    def compute_key_hash(self) -> None:
        """Compute the key hash of the entity.

        Note that untill an entity is stored in DB, the key_hash property is set to
        None. Therefor, to access the key_hash of a not-yet stored entity, one should
        use this method.
        """
        return sha256(
            self.HASH_SEPARATOR.join(self.business_key_values).encode()
        ).hexdigest()
