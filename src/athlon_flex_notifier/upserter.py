import contextlib
from datetime import datetime
from typing import TYPE_CHECKING, Any, TypeVar

from kink import inject
from sqlalchemy import Engine, update
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session

from athlon_flex_notifier.utils import now

if TYPE_CHECKING:
    from athlon_flex_notifier.models.base_model import BaseModel

T = TypeVar("T", bound="BaseModel")


class Upserter:
    entities: list[T]
    data: list[dict[str, Any]]
    key_hashes: list[str]
    attribute_hashes: list[str]
    session: Session | None = None
    database: Engine
    timestamp: datetime

    @inject
    def __init__(self, database: Engine, entities: list[T]) -> None:
        self.database = database
        self.entities = entities
        self.timestamp = now()
        self.data = [entity.model_dump() for entity in entities]
        self.key_hashes = [entity["key_hash"] for entity in entities]
        self.attribute_hashes = [entity["attribute_hash"] for entity in entities]
        self.data = [
            {**entity.model_dump(), "active_from": self.timestamp}
            for entity in entities
        ]

    def __del__(self) -> None:
        """Automatically close the session when the object is garbage collected."""
        if self.session:
            with contextlib.suppress(Exception):
                self.session.close()

    @property
    def entity_class(self) -> type[T]:
        if not self.entities:
            msg = "No entities provided"
            raise RuntimeError(msg)
        return type(self.entities[0])

    def scd2(self) -> list[T]:
        """Perform SCD2 upserts.

        This means:
        - Insert the entities into target.
        - Check for conflicts on the key hash:
            - If conflict:
                - If the attribute hash is the same, do nothing
                - Else:
                    - Close the existing record. ie set active_to
                    - Insert the new entity, with active_from now and active_to None
            - Else:
                - Insert the new entity, with active_from None and active_to None
        - For all entities in DB that are not in entities:
            - Close the existing record. ie set active_to and deleted_at
        todo: check https://blog.miguelgrinberg.com/post/implementing-the-soft-delete-pattern-with-flask-and-sqlalchemy
        todo: use below url for deleted at.
        https://theshubhendra.medium.com/mastering-soft-delete-advanced-sqlalchemy-techniques-4678f4738947
        """
        if not self.data:
            return []
        if not self.session:
            self.session = Session(self.database, expire_on_commit=False)
        # todo: exclude deleted and active filter where needed
        self.close_rows_of_updated_entities()
        self.delete_rows_of_removed_entities()
        self.create_rows_for_updated_and_new_entities()
        self.session.commit()
        self.session.close()
        # Reload from DB, to ensure all attributes are up-to-date
        result = self.entity_class.get(
            key_hashes=[row["key_hash"] for row in self.data]
        )
        if len(result) != len(self.data):
            msg = f"Upserted {len(result)} entities, expected {len(self.data)}"
            raise RuntimeError(msg)
        return result

    def close_rows_of_updated_entities(self) -> None:
        statement = (
            update(self.entity_class)
            .where(
                self.entity_class.key_hash.in_(self.key_hashes)
                and self.entity_class.attribute_hash.not_in(self.attribute_hashes)
                and self.entity_class.active_to.is_(None)
            )
            .values(active_to=self.timestamp)
        )
        self.session.exec(statement)

    def create_rows_for_updated_and_new_entities(self) -> None:
        statement = insert(self.entity_class).values(self.data)
        statement = statement.on_conflict_do_nothing(index_elements=["id"])
        self.session.exec(statement)

    def delete_rows_of_removed_entities(self) -> None:
        statement = (
            update(self.entity_class)
            .where(
                self.entity_class.key_hash.not_in(self.key_hashes)
                and self.entity_class.deleted_at.is_(None)
                and self.entity_class.active_to.is_(None)
            )
            .values(deleted_at=self.timestamp, active_to=self.timestamp)
        )
        self.session.exec(statement)
