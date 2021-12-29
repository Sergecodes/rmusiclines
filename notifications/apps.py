from django.apps import AppConfig


class Config(AppConfig):
    name = "notifications"

    def ready(self):
        import notifications.signals

