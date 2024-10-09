from sqlmodel import Field, SQLModel


class VehicleOption(SQLModel, table=True, table_name="vehicle_option"):
    __tablename__ = "vehicle_option"
    vehicle_id: str | None = Field(
        default=None, foreign_key="vehicle.id", primary_key=True
    )
    option_id: str | None = Field(
        default=None, foreign_key="option.id", primary_key=True
    )
