from django.db import models
from django.utils.translation import gettext_lazy as _

from .base.models import AbstractNotification


class Notification(AbstractNotification):
    GENERAL = 'G'       # general notifications
    MENTION = 'M'       # to users that were mentioned in comments(qa_site only)
    ACTIVITY = 'A'      # to post owners, when their post has an activity
    FLAG = 'F'          # to users whose post has been flagged
    REPORTED = 'R'      # moderators only, for reported posts
    FOLLOWING = 'FF'    # for users that are following a post

    CATEGORIES = (
        (GENERAL, _('General')),
        (MENTION, _('Mention')),
        (ACTIVITY, _('Activity')),
        (FLAG, _('Flag')),
        (FOLLOWING, _('Following')),
        (REPORTED, _('Reported'))
    )

    category = models.CharField(choices=CATEGORIES, default='G', max_length=2)
    # url to go to; useful for general notifications
    # no null=True needed since this inherits from the CharField
    follow_url = models.URLField(blank=True)
    # used in REPORTED notifications to check whether a post(flag) has been absolved or not
    # as said in the docs, "the default value of BooleanField is None when Field.default isn't defined."
    # we set null=True so it is nullable, to account for notifcations that don't use this field.
    absolved = models.BooleanField(null=True)

    class Meta(AbstractNotification.Meta):
        abstract = False



