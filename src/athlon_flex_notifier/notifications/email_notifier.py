import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from logging import Logger

from kink import inject

from athlon_flex_notifier.notifications.email.renderer import Renderer
from athlon_flex_notifier.notifications.notifier import Notifier


class EmailNotifier(Notifier):
    """Notify the user about new vehicles through email."""

    server: smtplib.SMTP

    @inject
    def __init__(self, logger: Logger, server: smtplib.SMTP) -> None:
        self.logger = logger
        self.server = server

    def notify(self) -> bool:
        message = MIMEMultipart()
        message["Subject"] = "Athlon: new vehicles available"
        message["From"] = os.environ["EMAIL_FROM"]
        message["To"] = os.environ["EMAIL_TO"]
        message.attach(MIMEText(self.renderer.render(), "html"))

        with self.server as server:
            server.sendmail(
                os.environ["EMAIL_FROM"],
                os.environ["EMAIL_TO"],
                message.as_string(),
            )
        return True

    @property
    def renderer(self) -> Renderer:
        return Renderer(vehicle_clusters=self.vehicle_clusters)
