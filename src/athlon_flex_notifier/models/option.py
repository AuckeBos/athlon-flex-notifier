from typing import TYPE_CHECKING

from athlon_flex_api.models.vehicle import Vehicle as VehicleBase
from sqlmodel import Field, Relationship

from athlon_flex_notifier.models.base_model import BaseModel

if TYPE_CHECKING:
    from athlon_flex_notifier.models.vehicle import Vehicle


class Option(BaseModel, table=True):
    id: str = Field(primary_key=True)
    externalId: str
    optionName: str
    included: bool
    vehicle_id: str = Field(primary_key=True, foreign_key="vehicle.id")
    vehicle: "Vehicle" = Relationship(back_populates="options")

    def from_base(option_base: VehicleBase.Option, vehicle: "Vehicle") -> "Option":
        data = {
            "id": option_base.id,
            "externalId": option_base.externalId,
            "optionName": option_base.optionName,
            "included": option_base.included,
            "vehicle_id": vehicle.id,
        }
        return Option(**data).upsert()
