from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _


class FlagConfig(AppConfig):
    name = 'flagging'

    def ready(self):
        import flagging.signals

        post_migrate.connect(flagging.signals.create_permission_groups, sender=self)
        post_migrate.connect(flagging.signals.adjust_flagged_content, sender=self)
