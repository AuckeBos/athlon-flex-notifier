from typing import TypeVar

from kink import inject
from sqlalchemy import Engine, insert, update
from sqlmodel import Session

from athlon_flex_notifier.models.base_model import BaseModel
from athlon_flex_notifier.utils import now

T = TypeVar("T", bound="BaseModel")


class Upserter:
    @inject
    def scd2(self, database: Engine, entities: list[T]) -> list[T]:
        """Perform SCD2 upserts.

        This means:
        - Insert the entities into target.
        - Check for conflicts on the key hash:
            - If conflict:
                - If the attribute hash is the same, do nothing
                - Else:
                    - Close the existing record. ie set active_to
                    - Insert the new entity, with active_from None and active_to None
            - Else:
                - Insert the new entity, with active_from None and active_to None
        - For all entities in DB that are not in entities:
            - Close the existing record. ie set active_to
            - Create a new record, with data of the old record, but is_deleted=True
        todo: check https://blog.miguelgrinberg.com/post/implementing-the-soft-delete-pattern-with-flask-and-sqlalchemy
        """
        if not entities:
            return []
        cls_ = type(entities[0])
        now_ = now()
        data = [{**entity.model_dump(), "active_from": now_} for entity in entities]
        with Session(database, expire_on_commit=False) as session:
            # deleted_at should be part of the attr hash
            # this ensures that if receive entity, new attr hash, hence close old insert new

            close_existing_insert_new = insert(cls_).values(data)
            close_existing_insert_new = close_existing_insert_new.on_conflict_do_update(
                index_elements=["key_hash"],
                set_={"active_to": now_},
                where=cls_.attribute_hash
                != close_existing_insert_new.excluded.attribute_hash,
            )
            session.exec(close_existing_insert_new)
            insert_for_updated_records = (
                insert(cls_).values(data).on_conflict_do_nothing(index_elements=["id"])
            )
            session.exec(insert_for_updated_records)
            close_deleted = (
                update(cls_)
                .where(
                    cls_.id.not_in([row["id"] for row in data])
                    and cls_.deleted_at.is_(None)
                )
                .values(active_to=now_)
            )
            # todo: check if session.exec actually returns the rrows or not
            # if not, load by id not in
            deleted_records = session.exec(close_deleted)
            insert_for_deleted_records = (
                insert(cls_)
                .values(
                    [
                        {**row.model_dump(), "deleted_at": deleted_records}
                        for row in data
                    ]
                )
                .on_conflict_do_nothing(index_elements=["id"])
            )
            session.exec(insert_for_deleted_records)

            session.commit()
        # Reload from DB, to ensure all attributes are up-to-date
        result = cls_.get(ids=[row["id"] for row in data])  # fix
        if len(result) != len(entities):
            msg = f"Upserted {len(result)} entities, expected {len(entities)}"
            raise RuntimeError(msg)
        return result

    @classmethod
    def upsert(cls, *entities: T) -> list[T]:
        """Upsert multiple entities into the database."""
        if not entities:
            return []
        data = [entity.model_dump() for entity in entities]
        with Session(di["database"], expire_on_commit=False) as session:
            stmt = insert(cls).values(data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["key_hash"],  # todo: fix, with scd2 upserter
                set_={
                    col: getattr(stmt.excluded, col)
                    for col in {*cls.attribute_keys(), "updated_at", "attribute_hash"}
                },
                where=cls.attribute_hash != stmt.excluded.attribute_hash,
            )
            session.exec(stmt)
            session.commit()
        # Reload from DB, to ensure all attributes are up-to-date
        result = cls.get(ids=[row["id"] for row in data])  # fix
        if len(result) != len(entities):
            msg = f"Upserted {len(result)} entities, expected {len(entities)}"
            raise RuntimeError(msg)
        return result
