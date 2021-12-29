from collections import namedtuple
from enum import IntEnum, unique
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .operations import FlagOperations
from ..managers import FlagInstanceManager, FlagManager

User = settings.AUTH_USER_MODEL


class Flag(models.Model, FlagOperations):
    """Used to add flag/moderation to a model"""
    
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
        Return if flag is flagged or not. Flag is considered flag if its count is > FLAGS_ALLOWED.
        Note that the flags state is updated when toggle_flagged_state() is called, 
        and the latter is called after every new FlagInstance... 
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
    # Reasons displayed when flagging an object
    FLAG_REASONS = [
        (1, _("Spam | Exists only to promote a service ")),
        (2, _("Abusive | Intended at promoting hatred")),
        (100, _('Something else'))
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
    date_flagged = models.DateTimeField(auto_now_add=True)
    reason = models.SmallIntegerField(choices=FLAG_REASONS, default=reason_values[0])
    info = models.TextField(blank=True)

    objects = FlagInstanceManager()

    def clean(self):
        # If something else is chosen, info should not be empty
        if self.reason == self.reason_values[-1] and not self.info:
            raise ValidationError(
                {
                    'info': ValidationError(
                        _('Please provide some information why you choose to report the content'),
                        code='required'
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'flagging\".\"flag_instance'
        ordering = ['-date_flagged']
        indexes = [
            models.Index(
                fields=['-date_flagged'],
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

