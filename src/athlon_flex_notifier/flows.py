from kink import di
from prefect import flow, serve, task
from prefect.client.schemas.schedules import CronSchedule

from athlon_flex_notifier.notifications.notifiers import Notifiers
from athlon_flex_notifier.vehicle_availability_service import (
    VehicleAvailabilityServices,
)


@task
def update_availabilities() -> None:
    """Update vehicles and vehicle availabilities."""
    di[VehicleAvailabilityServices].update_availabilities()


@task
def notify() -> None:
    """Notify the user about new vehicles."""
    di[Notifiers].notify()


@flow
def update_and_notify() -> None:
    """Update availabilities and notify the user."""
    update_availabilities()
    notify()


def work() -> None:
    """Create the deployments."""
    serve(
        update_and_notify.to_deployment(
            name="update_and_notify",
            version="2024.10.13",
            schedules=[
                CronSchedule(
                    cron="*/10 * * * *",
                )
            ],
        )
    )
