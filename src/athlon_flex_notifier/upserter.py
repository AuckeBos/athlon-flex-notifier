import contextlib
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
    session: Session | None = None
    database: Engine
    timestamp: datetime.datetime

    @inject
    def __init__(self, database: Engine, entities: list[T]) -> None:
        self.database = database
        self.entities = entities
        self.timestamp = now()
        self.data = [entity.model_dump() for entity in entities]
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

        Issue: need to attach event with the sessionmaker, but we use the SqlModel session.
        We do not need sqlmodel, so use sqlalchemy instead of sqlmodel ,then attach to sessionmaker do_orm_execute.
        """
        if not self.data:
            return []
        if not self.session:
            self.session = Session(self.database, expire_on_commit=False)

        self.close_existing_and_insert_new()
        self.insert_for_updated()
        self.delete_removed()
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
