from typing import TYPE_CHECKING

from athlon_flex_api.models.vehicle import Vehicle as VehicleBase
from sqlmodel import Field, SQLModel


if TYPE_CHECKING:
    from athlon_flex_notifier.models.vehicle import Vehicle


class Option(SQLModel, table=True):
    id: str = Field(primary_key=True)
    externalId: str
    optionName: str
    included: bool
    # vehicles: list["Vehicle"] = Relationship(
    #     back_populates="options", link_model=VehicleOption
    # )

    def from_base(option_base: VehicleBase.Option) -> "Option":
        return Option(
            id=option_base.id,
            externalId=option_base.externalId,
            optionName=option_base.optionName,
            included=option_base.included,
        )
