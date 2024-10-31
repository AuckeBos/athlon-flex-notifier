import contextlib
from datetime import datetime
from typing import TYPE_CHECKING, Any, TypeVar

from kink import inject
from sqlalchemy import Engine, and_, bindparam, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session

from athlon_flex_notifier.utils import now

if TYPE_CHECKING:
    from athlon_flex_notifier.models.base_model import BaseModel


T = TypeVar("T", bound="BaseModel")


@inject
class Upserter:
    """Upsert data into the database, using SCD2."""

    data: list[dict[str, Any]]
    entity_class: T
    session: Session | None = None
    timestamp: datetime

    @inject
    def upsert(self, entities: list[T] = None, database: Engine = None) -> dict[str, T]:
        """Upsert multiple entities into the database.

        - Update records in-place if scd1 attributes are updated
        - Update records by closing and creating new rows if scd2 attributes are updated

        Returns
        -------
        dict[str, T], maps key_hash the upserted entity

        """
        self.timestamp = now()
        self.data = [
            {**entity.model_dump(), "active_from": self.timestamp}
            for entity in entities
        ]
        if not self.data:
            return {}
        if len(entities):
            self.entity_class = type(entities[0])
        if not self.session:
            self.session = Session(database, expire_on_commit=False)
        self.scd1()
        self.scd2()
        self.session.commit()
        self.session.close()
        # Reload from DB, to ensure all attributes are up-to-date
        result = self.entity_class.get(key_hashes=self.key_hashes)
        if len(result) != len(self.data):
            msg = f"Found {len(result)} entities after upsert, expecteded {len(self.data)}"
            raise RuntimeError(msg)
        return {entity.key_hash: entity for entity in result}

    def scd1(self) -> None:
        """Update rows in the target in-place with updates of the scd1 attributes.

        Only update rows that already exist. New rows will be added by scd2. 1
        Only update rows if the scd1 hash has changed.
        Only update active rows
        """
        keys = [
            *self.entity_class.scd1_attribute_keys(),
            "key_hash",
            "attribute_hash_scd1",
        ]
        data = [{key: row[key] for key in keys} for row in self.data]
        statement = (
            update(self.entity_class)
            .where(
                and_(
                    self.entity_class.key_hash == bindparam("key_hash"),
                    self.entity_class.attribute_hash_scd1
                    != bindparam("attribute_hash_scd1"),
                    self.entity_class.active_to.is_(None),
                )
            )
            .values(**{key: bindparam(key) for key in keys})
            .execution_options(synchronize_session=False)
        )
        self.session.connection().execute(statement, data)

    @property
    def key_hashes(self) -> list[str]:
        return [row["key_hash"] for row in self.data]

    def scd2(self) -> None:
        """Update rows in the target in-place with updates of the scd2 attributes."""
        self.close_active_rows_of_updated_and_deleted_entities()
        self.create_rows_for_updated_and_new_entities()

    def close_active_rows_of_updated_and_deleted_entities(self) -> None:
        """Close all rows that are deleted or updated scd2.

        For updated entities, new rows are added in create_rows_for_updated_and_new_entities
        """
        statement = (
            update(self.entity_class)
            .where(
                and_(
                    self.scd2_attributes_updated_or_entity_deleted(),
                    self.entity_class.active_to.is_(None),  # Only close active rows
                )
            )
            .values(active_to=self.timestamp)
        )
        self.session.exec(statement)

    def scd2_attributes_updated_or_entity_deleted(self) -> ColumnElement:
        """A clause to check if the scd2 sttrs are updated or the entity is deleted.

        This is true if the key_hash-attribute_hash_scd2 combination is not in the new
        scd2 attributes. This happens that either the key_hash is not in the new key
        hashes (ie the entity is deleted),or the attribute_hash_scd2 is not in the
        new scd2 attributes (ie the entity is updated).
        """  # noqa: D401
        new_scd2 = [
            "-".join([row["key_hash"], row["attribute_hash_scd2"]]) for row in self.data
        ]
        existing_scd2 = func.CONCAT_WS(
            "-",
            self.entity_class.key_hash,
            self.entity_class.attribute_hash_scd2,
        )
        return existing_scd2.not_in(new_scd2)

    def create_rows_for_updated_and_new_entities(self) -> None:
        """For any row that is new or updated, create a new row in the target table.

        # A: Any key_hashes that did already exist will not be included in this list,
        because active_to is not None. Therefor, we will insert records for updated
        entites as well as new entities.
        """
        existing_active_key_hashes = [
            item[0]
            for item in self.session.exec(
                select(self.entity_class.key_hash).distinct()  # A
            ).all()
        ]
        new_and_updated_entities = [
            row
            for row in self.data
            if row["key_hash"] not in existing_active_key_hashes
        ]
        if not new_and_updated_entities:
            return
        statement = insert(self.entity_class).values(new_and_updated_entities)
        self.session.exec(statement)

    def __del__(self) -> None:
        """Automatically close the session when the object is garbage collected."""
        if self.session:
            with contextlib.suppress(Exception):
                self.session.close()
