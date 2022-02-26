from django.contrib.auth.models import Group
from django.db.models.query import QuerySet
from django.dispatch import Signal
from django.utils import timezone

from core.utils import get_content_type
from notifications.models.models import Notification


def notify_handler(verb, **kwargs):
    """
    Handler function to create Notification instance upon action signal call.
    """
    # Pull the options out of kwargs
    # kwargs.pop('signal', None)
    recipient = kwargs.pop('recipient')
    actor = kwargs.pop('sender')
    optional_objs = [
        (kwargs.pop(opt, None), opt)
        for opt in ('target', 'action_object')
    ]
    description = kwargs.pop('description', '')
    timestamp = kwargs.pop('timestamp', timezone.now())
    level = kwargs.pop('level', Notification.INFO)
    ## added fields
    category = kwargs.pop('category')

    # Check if User or Group
    if isinstance(recipient, Group):
        recipients = recipient.user_set.all()
    elif isinstance(recipient, (QuerySet, list)):
        recipients = recipient
    else:
        recipients = [recipient]

    new_notifications = []

    for recipient in recipients:
        newnotify = Notification(
            recipient=recipient,
            actor_content_type=get_content_type(actor),
            actor_object_id=actor.pk,
            verb=str(verb),
            description=description,
            timestamp=timestamp,
            level=level,
            category=category,
        )

        # Set optional objects
        for obj, opt in optional_objs:
            if obj is not None:
                setattr(newnotify, '%s_object_id' % opt, obj.pk)
                setattr(
                    newnotify, 
                    '%s_content_type' % opt,
                    get_content_type(obj)
                )

        newnotify.save()
        new_notifications.append(newnotify)

    return new_notifications


# Connect the signal
notify = Signal()

# See https://docs.djangoproject.com/en/3.2/topics/signals/#preventing-duplicate-signals
notify.connect(notify_handler, dispatch_uid='my_unique_identifier')

