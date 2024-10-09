from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from athlon_flex_notifier.models.vehicle_option import VehicleOption

if TYPE_CHECKING:
    from athlon_flex_notifier.models.vehicle import Vehicle


class Option(SQLModel, table=True):
    id: str = Field(primary_key=True)
    externalId: str
    optionName: str
    included: bool
    vehicles: list["Vehicle"] = Relationship(
        back_populates="options", link_model=VehicleOption
    )
