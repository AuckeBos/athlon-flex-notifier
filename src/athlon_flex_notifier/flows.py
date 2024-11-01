from kink import di
from prefect import flow, serve, task
from prefect.client.schemas.schedules import CronSchedule

from athlon_flex_notifier.notifications.notifiers import Notifiers
from athlon_flex_notifier.refresher import (
    Refresher,
)


@task
def refresh() -> None:
    """Update the database with the current vehicles."""
    di[Refresher].refresh()


@task
def notify() -> None:
    """Notify the user about new vehicles."""
    di[Notifiers].notify()


@flow
def refresh_and_notify() -> None:
    """Update availabilities and notify the user."""
    refresh()
    notify()


def work() -> None:
    """Create the deployments."""
    serve(
        refresh_and_notify.to_deployment(
            name="refresh_and_notify",
            version="2024.11.03",
            schedules=[
                CronSchedule(
                    cron="*/10 * * * *",
                )
            ],
        )
    )
