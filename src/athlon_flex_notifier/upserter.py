import contextlib
from datetime import datetime
from logging import Logger
from typing import TYPE_CHECKING, Any, TypeVar

from kink import inject
from sqlalchemy import Engine, and_, bindparam, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session

from athlon_flex_notifier.utils import now

if TYPE_CHECKING:
    from athlon_flex_notifier.models.tables.base_table import BaseTable


T = TypeVar("T", bound="BaseTable")


@inject
class Upserter:
    """Upsert data into the database, using SCD2."""

    data: list[dict[str, Any]]
    logger: Logger
    entity_class: T
    session: Session | None = None
    timestamp: datetime

    @inject
    def upsert(
        self, entities: list[T], database: Engine, logger: Logger
    ) -> dict[str, T]:
        """Upsert multiple entities into the database.

        - Update records in-place if scd1 attributes are updated
        - Update records by closing and creating new rows if scd2 attributes are updated

        Returns
        -------
        dict[str, T], maps key_hash the upserted entity

        """
        self.timestamp = now()
        self.logger = logger
        self.data = [
            {**entity.model_dump(), "active_from": self.timestamp}
            for entity in entities
        ]
        if not self.data:
            self.logger.error("No data to upsert")
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
            msg = f"Found {len(result)} entities after upsert, expecteded {len(self.data)}"  # noqa: E501
            raise RuntimeError(msg)
        return {entity.key_hash: entity for entity in result}

    def scd1(self) -> None:
        """Update rows in the target in-place with updates of the scd1 attributes.

        Only update rows that already exist. New rows will be added by scd2.
        Only update rows if the scd1 hash has changed.
        Only update active rows
        Only set scd1 attributes and attribute_hash_scd1
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
        self.close_active_rows_of_updated_entities()
        self.close_active_rows_of_deleted_entities()
        self.create_rows_for_updated_and_new_entities()

    def close_active_rows_of_updated_entities(self) -> None:
        """Close active rows that have changed scd2 attributes.

        Closing means setting active_to to the current timestamp.
        Only close rows where the key_hash still exsits, and the scd2 hash has changed
        """
        keys = ["key_hash", "attribute_hash_scd2"]
        data = [{f"{key}_": row[key] for key in keys} for row in self.data]
        statement = (
            update(self.entity_class)
            .where(
                and_(
                    self.entity_class.key_hash == bindparam("key_hash_"),
                    self.entity_class.attribute_hash_scd2
                    != bindparam("attribute_hash_scd2_"),
                    self.entity_class.active_to.is_(None),
                )
            )
            .values(
                active_to=self.timestamp,
            )
            .execution_options(synchronize_session=False)
        )
        self.session.connection().execute(statement, data)

    def close_active_rows_of_deleted_entities(self) -> None:
        """Close active rows that have been deleted.

        A row is deleted if the key_hash is not in the new data.
        """
        new_key_hashes = [row["key_hash"] for row in self.data]
        statement = (
            update(self.entity_class)
            .where(
                and_(
                    self.entity_class.key_hash.not_in(new_key_hashes),
                    self.entity_class.active_to.is_(None),
                )
            )
            .values(active_to=self.timestamp)
        )
        self.session.exec(statement)

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
