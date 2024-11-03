from kink import inject
from pydantic import BaseModel
from sqlalchemy import Engine, text
from sqlmodel import Session


class BaseView(BaseModel):
    """Pydantic model to hold rows in a view."""

    @classmethod
    @inject
    def all(cls, database: Engine) -> list["BaseView"]:
        """Get all rows of the view."""
        query = f"SELECT * FROM {cls.view_name()}"  # noqa: S608
        with Session(database) as session:
            query_result = session.exec(text(query)).all()
            return [cls(**row._asdict()) for row in query_result]

    @staticmethod
    def view_name() -> str:
        raise NotImplementedError
