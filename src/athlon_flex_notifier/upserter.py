from datetime import datetime
from typing import Any, TypeVar

from kink import inject
from sqlalchemy import Engine, insert, update
from sqlmodel import Session

from athlon_flex_notifier.models.base_model import BaseModel
from athlon_flex_notifier.utils import now

T = TypeVar("T", bound="BaseModel")


class Upserter:
    entities: list[T]
    data: list[dict[str, Any]]
    session: Session
    timestamp: datetime.datetime

    @inject
    def __init__(self, database: Engine, entities: list[T]) -> None:
        self.entities = entities
        self.session = Session(database, expire_on_commit=False)
        self.timestamp = now()
        self.data = [entity.model_dump() for entity in entities]
        self.data = [
            {**entity.model_dump(), "active_from": self.timestamp}
            for entity in entities
        ]

    def __del__(self) -> None:
        """Automatically close the session when the object is garbage collected."""
        self._await(self.session.close())

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
        """
        if not self.data:
            return []

        self.close_existing_and_insert_new()
        self.insert_for_updated()
        self.delete_removed()
        self.session.commit()
        self.session.close()
        # Reload from DB, to ensure all attributes are up-to-date
        # todo: never load deleted records (add in base query)
        result = self.entity_class.get(ids=[row["id"] for row in self.data])  # fix
        if len(result) != len(self.data):
            msg = f"Upserted {len(result)} entities, expected {len(self.data)}"
            raise RuntimeError(msg)
        return result

    def close_existing_and_insert_new(self) -> None:
        statement = insert(self.entity_class).values(self.data)
        statement = statement.on_conflict_do_update(
            index_elements=["key_hash"],
            set_={"active_to": self.timestamp},
            where=(
                self.entity_class.attribute_hash != statement.excluded.attribute_hash
                and statement.excluded.active_to.is_(None)
            ),
        )
        self.session.exec(statement)

    def insert_for_updated(self) -> None:
        statement = insert(self.entity_class).values(self.data)
        statement = statement.on_conflict_do_nothing(index_elements=["id"])
        self.session.exec(statement)

    def delete_removed(self) -> None:
        statement = (
            update(self.entity_class)
            .where(
                self.entity_class.key_hash.not_in(
                    [row["key_hash"] for row in self.data]
                )
                and self.entity_class.deleted_at.is_(None)
                and self.entity_class.active_to.is_(None)
            )
            .values(deleted_at=self.timestamp, active_to=self.timestamp)
        )
        self.session.exec(statement)
