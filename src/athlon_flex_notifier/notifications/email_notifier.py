from athlon_flex_notifier.notifications.notifier import Notifier


class EmailNotifier(Notifier):
    """Notify by email."""

    def notify(self) -> bool:
        raise NotImplementedError
