from collections.abc import Iterable
from datetime import datetime
from enum import Enum
from hashlib import sha256
from typing import ClassVar, TypeVar
from uuid import UUID, uuid4

from kink import inject
from pydantic import field_serializer
from sqlalchemy import UUID as SQLAlchemyUUID  # noqa: N811
from sqlalchemy import DateTime, Engine, select
from sqlmodel import Field, Session, SQLModel, func

T = TypeVar("T", bound="BaseTable")


class LoadType(Enum):
    """Indicates how to upsert a new batch of entities."""

    FULL_LOAD = 1
    DELTA_WITHOUT_DELETE = 2
    # Not yet supported
    DELTA_WITH_DELETE = 3


class BaseTable(SQLModel):
    """A Base class for SQLModel.

    Implementing classes MUST define business_keys, and
    CAN define scd1_attribute_keys (all attributes are scd2 by default).

    Extends the SQLModel class with additional methods.

    Attributes:
        LOAD_TYPE: ClassVar[LoadType] = LoadType.FULL_LOAD
            Defines how a new batch should be processed. Used by
            Upserter.

        HASH_SEPARATOR: ClassVar[str] = "-"
            Separates values when computing hashes

        id: UUID
            Primary key. Generated when instantated.
        key_hash: str
            Hash of the business keys. Computed when upserted. Before store in DB,
            this property is None.

        attribute_hash_scd1: str
            Hash of the scd1 attributes. Computed when upserted. Before store in DB,
            this property is None.
        attribute_hash_scd2: str
            Hash of the scd2 attributes. Computed when upserted. Before store in DB,
            this property is None.

        active_from: datetime
            Start date for scd2. Is required, must be set in Python.
        active_to: datetime
            End date for scd2. None upon creation. Set when updated or deleted.
        is_current: bool
            True if this record is the current record of this entity.

        created_at: datetime
            Creation date of the record. Set by the server.

        updated_at: datetime
            Last update date of the record. Auto updated by server.

    KNOWN ISSUES:
        - sort_order doesn't work: https://github.com/fastapi/sqlmodel/issues/542
            Therefor, computed columns are the first instead of the last cols.
            Kept in code, for future reference
        - alias doesn't work: https://github.com/fastapi/sqlmodel/discussions/725
            https://stackoverflow.com/questions/77819208/how-can-i-use-alias-in-sqlmodel-library
            Removed from code, to prevent unclarity. When fixed: Prefix
            computed cols with _.

    """

    LOAD_TYPE: ClassVar[LoadType] = LoadType.FULL_LOAD

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
    attribute_hash_scd1: str | None = Field(
        default=None,
        sa_column_kwargs={"sort_order": 91},
    )
    attribute_hash_scd2: str | None = Field(
        default=None,
        sa_column_kwargs={"sort_order": 92},
    )

    active_from: datetime | None = Field(
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"sort_order": 93},
    )
    active_to: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"sort_order": 94},
    )
    is_current: bool = Field(
        default=True,
        sa_column_kwargs={"sort_order": 95},
    )
    created_at: datetime | None = Field(
        exclude=True,
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),
            "sort_order": 96,
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
            "sort_order": 97,
        },
    )

    @classmethod
    def business_keys(cls) -> list[str]:
        """A model must define it's business keys using this property.

        A model MUST NOT set the fields as primary key, because the
        id is used as primary key.
        """  # noqa: D401
        msg = f"Must define primary keys for {cls.__name__}"
        raise NotImplementedError(msg)

    @classmethod
    def scd1_attribute_keys(cls) -> list[str]:
        """A model can define it's scd1 attributes using this property.

        By default, all non-business keys are scd2 attributes. This means
        that history will be kept if a value changes for such an attribute.
        If the entity contains attributes for which we do not want to
        preserve history, but for which new values should be
        overwritten, one should use this property.

        Example: VehicleCluster.first_vehicle_id. Preserving history
        for this key would mean a new version of a cluster whenever
        the first vehicle is leased; this doesn't make any sense.

        Todo: always include all foreign keys in this list.
        """  # noqa: D401
        return []

    @classmethod
    @inject
    def get(cls: T, database: Engine, *, key_hashes: Iterable[str]) -> list[T]:
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
    def generated_keys(cls) -> list[str]:
        return sorted(
            [
                "id",
                "key_hash",
                "attribute_hash_scd1",
                "attribute_hash_scd2",
                "created_at",
                "updated_at",
                "active_from",
                "active_to",
                "is_current",
            ]
        )

    @classmethod
    def attribute_keys(cls) -> set[str]:
        return set(cls.keys()) - set(cls.business_keys()) - set(cls.generated_keys())

    @classmethod
    def scd2_attribute_keys(cls) -> set[str]:
        return set(cls.attribute_keys()) - set(cls.scd1_attribute_keys())

    @property
    def scd1_attribute_values(self) -> list[str]:
        return [str(getattr(self, key)) for key in sorted(self.scd1_attribute_keys())]

    @property
    def scd2_attribute_values(self) -> list[str]:
        return [str(getattr(self, key)) for key in sorted(self.scd2_attribute_keys())]

    @property
    def business_key_values(self) -> list[str]:
        """Get the primary key values of the entity."""
        return [str(getattr(self, key)) for key in sorted(self.business_keys())]

    @property
    def attribute_values(self) -> list[str]:
        """Get the attribute values of the entity."""
        return [str(getattr(self, key)) for key in sorted(self.attribute_keys())]

    @field_serializer("attribute_hash_scd2")
    def _attribute_hash_scd2_serializer(self, _: str | None) -> str:
        return sha256(
            self.HASH_SEPARATOR.join(self.scd2_attribute_values).encode()
        ).hexdigest()

    @field_serializer("attribute_hash_scd1")
    def _attribute_hash_scd1_serializer(self, _: str | None) -> str:
        return sha256(
            self.HASH_SEPARATOR.join(self.scd1_attribute_values).encode()
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
