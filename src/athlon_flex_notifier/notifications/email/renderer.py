from pathlib import Path
from typing import ClassVar

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from athlon_flex_notifier.models.vehicle_cluster import VehicleCluster


class Renderer(BaseModel):
    """Render the email template, showing available vehicles."""

    vehicle_clusters: list[VehicleCluster]
    TEMPLATE_FOLDER: ClassVar[str] = Path(__file__).parent / "templates"
    TEMPLATE_FILE: ClassVar[str] = "email.html"

    def min_net_cost_of(self, vehicle_cluster: VehicleCluster) -> float:
        return min(
            availability.vehicle.net_cost_in_euro_per_month
            for availability in vehicle_cluster.unnotified_availabilities
        )

    def max_net_cost_of(self, vehicle_cluster: VehicleCluster) -> float:
        return max(
            availability.vehicle.net_cost_in_euro_per_month
            for availability in vehicle_cluster.unnotified_availabilities
        )

    def render(self) -> str:
        environment = Environment(
            loader=FileSystemLoader(str(self.TEMPLATE_FOLDER)), autoescape=True
        )
        template = environment.get_template(self.TEMPLATE_FILE)
        return template.render(renderer=self)
