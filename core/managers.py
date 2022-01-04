from actstream.managers import (
    ActionManager as BaseActionManager, 
    stream
)
# from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class ActionManager(BaseActionManager):
    """
    Interface for querying activity data from the database.
    (via django-activity-stream)
    """

    @stream
    def mystream(self, obj, verb='posted', time=None):
        if not time:
            time = timezone.now()
        return obj.actor_actions.filter(verb=verb, timestamp__lte=time)


