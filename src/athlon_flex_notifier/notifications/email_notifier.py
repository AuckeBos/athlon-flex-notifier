from athlon_flex_notifier.notifications.notifier import Notifier


class EmailNotifier(Notifier):
    def notify(self) -> bool:
        raise NotImplementedError
