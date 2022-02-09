from collections import namedtuple
from enum import IntEnum, unique
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from .operations import FlagOperations
from ..managers import FlagInstanceManager, FlagManager

User = settings.AUTH_USER_MODEL


class Flag(models.Model, FlagOperations):
    """
    Used to add flag/moderation to a model. 
    Use on models with a "poster" field or attribute and corresponding 'poster_id' attribute. 
    This attribute is used to get the user that created the flagged content.
    """
    
    @unique
    class State(IntEnum):
        UNFLAGGED = 1
        FLAGGED = 2
        REJECTED = 3
        NOTIFIED = 4
        RESOLVED = 5

    STATE_CHOICES = [
        (State.UNFLAGGED.value, _('Unflagged')),
        (State.FLAGGED.value, _('Flagged')),
        (State.REJECTED.value, _('Flag rejected by the moderator')),
        (State.RESOLVED.value, _('Content modified by the author')),
        (State.NOTIFIED.value, _('Creator notified')),
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    # Flagged object
    content_object = GenericForeignKey('content_type', 'object_id')
    # User who has the post
    creator = models.ForeignKey(
        User, 
        related_name='flags_against', 
        null=True, blank=True, 
        on_delete=models.CASCADE
    )
    state = models.SmallIntegerField(choices=STATE_CHOICES, default=State.UNFLAGGED.value)
    moderator = models.ForeignKey(
        User, 
        null=True, blank=True, 
        related_name='flags_moderated', 
        on_delete=models.SET_NULL
    )
    count = models.PositiveIntegerField(default=0)

    objects = FlagManager()

    @property
    def is_flagged(self):
        """
        Return if flag is flagged or not. Flag is considered flag 
        if its count is > MAX_FLAGS_ALLOWED.
        Note that the flags state is updated when toggle_flagged_state() is called, 
        and the latter is called after every new FlagInstance is created.
        """
        return self.state != self.State.UNFLAGGED.value

    class Meta:
        db_table = 'flagging\".\"flag'
        verbose_name = _('Flag')
        constraints = [
            models.UniqueConstraint(
                fields=['content_type', 'object_id'],
                name='unique_content_type_and_object_id'
            )
        ]


class FlagInstance(models.Model):
    # Flag reasons
    @unique
    class FlagReason(IntEnum):
        SPAM = 1
        EXPLICIT = 2
        HATE_SPEECH = 3
        VIOLENCE = 4
        HARASSMENT = 5
        
    # Reasons displayed when flagging an object
    FLAG_REASONS = [
        (FlagReason.SPAM.value, _('Unwanted commercial content or spam')),
        (FlagReason.EXPLICIT.value, _('Pornography or sexually explicit content')),
        (FlagReason.HATE_SPEECH.value, _('Hate speech or graphic violence')),
        (FlagReason.VIOLENCE.value, _('Abusive or intended at promoting hatred')),
        (FlagReason.HARASSMENT.value, _('Harassment or bullying')),
    ]

    # Make a named tuple
    Reasons = namedtuple('Reason', ['value', 'reason'])

    # Construct the list of named tuples
    reasons = []
    for reason in FLAG_REASONS:
        reasons.append(Reasons(*reason))

    reason_values = [reason.value for reason in reasons]

    flag = models.ForeignKey(
        Flag, 
        related_name='flags', 
        related_query_name='flag_instance',
        on_delete=models.CASCADE,
        db_column='flag_id'
    )
    # User that created the flag
    user = models.ForeignKey(
        User, 
        related_name='created_flag_instances', 
        related_query_name='flag_instance',
        on_delete=models.CASCADE
    )
    flagged_on = models.DateTimeField(auto_now_add=True, editable=False)
    reason = models.SmallIntegerField(choices=FLAG_REASONS, default=reason_values[0])

    objects = FlagInstanceManager()

    class Meta:
        db_table = 'flagging\".\"flag_instance'
        ordering = ['-flagged_on']
        indexes = [
            models.Index(
                fields=['-flagged_on'],
                name='flag_instance_date_desc_idx'
            )
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['flag', 'user'],
                name='unique_user_and_flag_instance'
            )
        ]
        verbose_name = _('Flag Instance')
        verbose_name_plural = _('Flag Instances')

