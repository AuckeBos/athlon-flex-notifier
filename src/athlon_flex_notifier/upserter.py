import contextlib
from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING, Any, TypeVar

from kink import inject
from sqlalchemy import Engine, and_, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session

from athlon_flex_notifier.utils import now

if TYPE_CHECKING:
    from athlon_flex_notifier.models.base_model import BaseModel

T = TypeVar("T", bound="BaseModel")


class Upserter:
    """Upsert data into the database, using SCD2."""

    data: list[dict[str, Any]]
    entity_class: T
    session: Session | None = None
    database: Engine
    timestamp: datetime

    @inject
    def __init__(self, database: Engine, entities: list[T]) -> None:
        """Initialize the upserter.

        Dump the entities into a list of dicts, setting the active_from timestamp.
        """
        self.database = database
        self.timestamp = now()
        self.data = [
            {**entity.model_dump(), "active_from": self.timestamp}
            for entity in entities
        ]
        if len(entities) > 1:
            self.entity_class = type(entities[0])

    def scd2(self) -> dict[str, T]:
        """Perform SCD2 upserts.

        This means:
        - For all entities in target:
            - If key_hash not in source, the entity is deleted
                - Set active_to
            - If attribute_hash not in source, the entity is updated
                - Set active_to
        - For all entities in source:
            - If key hash not in target (with filter on active_to),
                the entity is inserted or updated
                - Insert record, with active_from

        Returns
        -------
        dict[str, T], maps key_hash the upserted entity

        """
        if not self.data:
            return []
        if not self.session:
            self.session = Session(self.database, expire_on_commit=False)
        self.close_active_rows_of_updated_and_deleted_entities()
        self.create_rows_for_updated_and_new_entities()
        self.session.commit()
        self.session.close()
        # Reload from DB, to ensure all attributes are up-to-date
        result = self.entity_class.get(key_hashes=self.key_hashes)
        if len(result) != len(self.data):
            msg = f"Upserted {len(result)} entities, expected {len(self.data)}"
            raise RuntimeError(msg)
        return {entity.key_hash: entity for entity in result}

    def close_active_rows_of_updated_and_deleted_entities(self) -> None:
        statement = (
            update(self.entity_class)
            .where(
                and_(
                    # todo: when scd1 and scd2 are supported, this doesnt work
                    # we should check for the concat of key,att hash instead
                    or_(
                        # Is deleted
                        self.entity_class.key_hash.not_in(self.key_hashes),
                        # Is updated
                        self.entity_class.attribute_hash.not_in(self.attribute_hashes),
                    ),
                    # Only close active rows
                    self.entity_class.active_to.is_(None),
                )
            )
            .values(active_to=self.timestamp)
        )
        self.session.exec(statement)

    @cached_property
    def key_hashes(self) -> list[str]:
        return [row["key_hash"] for row in self.data]

    @cached_property
    def attribute_hashes(self) -> list[str]:
        return [row["attribute_hash"] for row in self.data]

    def create_rows_for_updated_and_new_entities(self) -> None:
        existing_active_key_hashes = [
            item[0]
            for item in self.session.exec(
                select(self.entity_class.key_hash).distinct()
            ).all()
        ]
        new_and_updated_entities = [
            row
            for row in self.data
            if row["key_hash"] not in existing_active_key_hashes
        ]
        if new_and_updated_entities:
            self.session.exec(
                insert(self.entity_class).values(new_and_updated_entities)
            )

    def __del__(self) -> None:
        """Automatically close the session when the object is garbage collected."""
        if self.session:
            with contextlib.suppress(Exception):
                self.session.close()
