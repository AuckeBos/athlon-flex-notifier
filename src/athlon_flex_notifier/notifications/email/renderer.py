from pathlib import Path
from typing import ClassVar

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from athlon_flex_notifier.models.tables.vehicle_cluster import VehicleCluster
from athlon_flex_notifier.models.views.vehicle_availability import VehicleAvailability
from athlon_flex_notifier.notifications.notifier import Notifier


class Renderer(BaseModel):
    """Render the email template, showing available vehicles."""

    class Config:  # noqa: D106
        arbitrary_types_allowed = True

    notifier: Notifier
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

    def round_or_na(self, value: float) -> str:
        if value is None:
            return "N/A"
        return f"{value:.2f}"

    def render(self) -> str:
        environment = Environment(
            loader=FileSystemLoader(str(self.TEMPLATE_FOLDER)), autoescape=True
        )
        template = environment.get_template(self.TEMPLATE_FILE)
        return template.render(renderer=self)

    @property
    def vehicle_clusters(self) -> list[VehicleCluster]:
        return self.notifier.vehicle_clusters

    def availabilities_for_cluster(
        self, cluster: VehicleCluster
    ) -> list[VehicleAvailability]:
        return self.notifier.availabilities_for_cluster(cluster)
