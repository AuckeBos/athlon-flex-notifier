from datetime import datetime
from functools import cached_property
from typing import TypeVar

from kink import di, inject
from sqlalchemy import DateTime, Engine, inspect, select
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Field, Relationship, Session, SQLModel, func

T = TypeVar("T", bound="BaseModel")


class BaseModel(SQLModel):
    """A Base class for SQLModel.

    Extends the SQLModel class with additional methods.
    """

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
        # https://stackoverflow.com/questions/25955200/sqlalchemy-performing-a-bulk-upsert-if-exists-update-else-insert-in-postgr
        new_entities = []
        for entity in entities:
            # entity.first_vehicle_id = "test" + str(entity.first_vehicle_id)
            new_entities.append(entity)
        data = [entity.model_dump() for entity in new_entities]
        with Session(di["database"], expire_on_commit=False) as session:
            # todo: fix issue: updated_at not updated
            cols = set(cls.keys()) - set(cls.primary_keys()) - {"created_at"}
            stmt = insert(cls).values(data)
            stmt = stmt.on_conflict_do_update(
                index_elements=cls.primary_keys(),
                set_={col: getattr(stmt.excluded, col) for col in cols},
            )
            session.exec(stmt)
            session.commit()
        return entities

    @classmethod
    def upsert_relationships(cls: T, *entities: T) -> list[T]:
        relationships = T.relationships
        for relationship in relationships:
            cls.upsert_relationships(*entities, relationship=relationship)

    @classmethod
    def upsert_relationships(
        cls: T, *entities: T, relationship: Relationship
    ) -> list[T]:
        childs = [entity.getattr(relationship.key) for entity in entities]
        test = ""

    @classmethod
    @inject
    def all(cls: T, database: Engine) -> list[T]:
        """Load all entities from the database."""
        with Session(database) as session:
            return [item[0] for item in session.exec(select(cls)).unique().all()]

    @classmethod
    def primary_keys(cls) -> list[str]:
        """Get the primary keys of the entity."""
        return [key.key for key in cls.__table__.primary_key.columns]

    @classmethod
    def keys(cls) -> list[str]:
        """Get the keys of the entity."""
        return [key.key for key in cls.__table__.c]

    @cached_property
    def primary_key_values(self) -> list[str]:
        """Get the primary key values of the entity."""
        return [str(getattr(self, key)) for key in self.primary_keys]

    @cached_property
    def relationships(self) -> list[Relationship]:
        """Get the relationships of the entity."""
        return inspect(self).mapper.relationships.values()
