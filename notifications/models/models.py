from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey 
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from notifications import settings as notifications_settings
from .operations import NotificationOperations


def is_soft_delete():
    return notifications_settings.get_config()['SOFT_DELETE']

def assert_soft_delete():
    if not is_soft_delete():
        msg = "To use 'deleted' field, please set 'SOFT_DELETE'=True in settings. \
        Otherwise NotificationQuerySet.unread and NotificationQuerySet.read \
        do NOT filter by 'deleted' field."

        raise ImproperlyConfigured(msg)


class NotificationQuerySet(QuerySet):
    """ Notification QuerySet """

    def unsent(self):
        return self.filter(emailed=False)

    def sent(self):
        return self.filter(emailed=True)

    def unread(self, include_deleted=False):
        """Return only unread items in the current queryset"""
        if is_soft_delete() and not include_deleted:
            return self.filter(unread=True, deleted=False)

        # When SOFT_DELETE=False, developers are supposed NOT to touch 'deleted' field.
        # In this case, to improve query performance, don't filter by 'deleted' field
        return self.filter(unread=True)

    def read(self, include_deleted=False):
        """Return only read items in the current queryset"""
        if is_soft_delete() and not include_deleted:
            return self.filter(unread=False, deleted=False)

        # When SOFT_DELETE=False, developers are supposed NOT to touch 'deleted' field.
        # In this case, to improve query performance, don't filter by 'deleted' field
        return self.filter(unread=False)

    def mark_all_as_read(self, recipient=None):
        """
        Mark as read any unread messages in the current queryset.
        Optionally, filter these by recipient first.
        """
        # We want to filter out read ones, as later we will store
        # the time they were marked as read.
        qset = self.unread(True)
        if recipient:
            qset = qset.filter(recipient=recipient)

        return qset.update(unread=False)

    def mark_all_as_unread(self, recipient=None):
        """
        Mark as unread any read messages in the current queryset.
        Optionally, filter these by recipient first.
        """
        qset = self.read(True)

        if recipient:
            qset = qset.filter(recipient=recipient)

        return qset.update(unread=True)

    def deleted(self):
        """Return only deleted items in the current queryset"""
        assert_soft_delete()
        return self.filter(deleted=True)

    def active(self):
        """Return only active(un-deleted) items in the current queryset"""
        assert_soft_delete()
        return self.filter(deleted=False)

    def mark_all_as_deleted(self, recipient=None):
        """
        Mark current queryset as deleted.
        Optionally, filter by recipient first.
        """
        assert_soft_delete()
        qset = self.active()
        if recipient:
            qset = qset.filter(recipient=recipient)

        return qset.update(deleted=True)

    def mark_all_as_active(self, recipient=None):
        """
        Mark current queryset as active(un-deleted).
        Optionally, filter by recipient first.
        """
        assert_soft_delete()
        qset = self.deleted()
        if recipient:
            qset = qset.filter(recipient=recipient)

        return qset.update(deleted=False)

    def mark_as_unsent(self, recipient=None):
        qset = self.sent()
        if recipient:
            qset = qset.filter(recipient=recipient)
        return qset.update(emailed=False)

    def mark_as_sent(self, recipient=None):
        qset = self.unsent()
        if recipient:
            qset = qset.filter(recipient=recipient)
        return qset.update(emailed=True)


class Notification(models.Model, NotificationOperations):
    """
    Action model describing the actor acting out a verb (on an optional
    target).
    Nomenclature based on http://activitystrea.ms/specs/atom/1.0/

    Generalized Format::

        <actor> <verb> <time>
        <actor> <verb> <target> <time>
        <actor> <verb> <action_object> <target> <time>

    Examples::

        <justquick> <reached level 60> <1 minute ago>
        <brosner> <commented on> <pinax/pinax> <2 hours ago>
        <washingtontimes> <started follow> <justquick> <8 minutes ago>
        <mitsuhiko> <closed> <issue 70> on <mitsuhiko/flask> <about 2 hours ago>

    Unicode Representation::

        justquick reached level 60 1 minute ago
        mitsuhiko closed issue 70 on mitsuhiko/flask 3 hours ago

    HTML Representation::

        <a href="http://oebfare.com/">brosner</a> commented on 
        <a href="http://github.com/pinax/pinax">pinax/pinax</a> 2 hours ago # noqa

    """

    SUCCESS = 'S'
    INFO = 'I'
    WARNING = 'W'
    ERROR = 'E'

    LEVEL_CODES = (
        (SUCCESS, _('Success')),
        (INFO, _('Info')),
        (WARNING, _('Warning')),
        (ERROR, _('Error'))
    )


    ACCOUNT = 'A'       # related to users accounts
    GENERAL = 'G'       # general notifications
    MENTION = 'M'       # to users that were mentioned in a post
    FLAG = 'F'          # to users whose post has been flagged 
                        # (may be n times, telling them to modify it)
    FOLLOW = 'FO'       # when a user follows another user
    REPORTED = 'R'      # moderators only, for reported posts
    RATING = 'RA'       # when user's post is rated
    COMMENT = 'C'       # when a user's post is commented on
    REPOST = 'RP'       # when a user's post is retweeted
    COMMENT_LIKE = 'CL' # when a user's comment is liked

    NOTIFICATION_CATEGORIES = (
        (GENERAL, _('General')),
        (ACCOUNT, _('Account')),
        (MENTION, _('Mention')),
        (FLAG, _('Flag')),
        (FOLLOW, _('Follow')),
        (REPORTED, _('Reported to moderator')),
        (RATING, _('Post rating')),
        (COMMENT, _('Comment')),
        (REPOST, _('Repost')),
        (COMMENT_LIKE, _('Comment like'))
    )

    level = models.CharField(choices=LEVEL_CODES, default=INFO, max_length=2)
    category = models.CharField(choices=NOTIFICATION_CATEGORIES, max_length=2)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='notifications',
        related_query_name='notification',
        on_delete=models.CASCADE,
        db_column='recipient_id'
    )
    actor_content_type = models.ForeignKey(
        ContentType, 
        related_name='notify_actor', 
        on_delete=models.CASCADE
    )
    # Use CharField so as to be able to point to an id of any type(int, uid, etc..)
    actor_object_id = models.CharField(max_length=255)
    actor = GenericForeignKey('actor_content_type', 'actor_object_id')

    verb = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    target_content_type = models.ForeignKey(
        ContentType,
        related_name='notify_target',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    # The target_content_type is optional so set this field optional via blank=True
    # No need to set null to True since we've set that on the content type.
    # and a pk can't be null
    target_object_id = models.CharField(max_length=255, blank=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')

    action_object_content_type = models.ForeignKey(
        ContentType, 
        related_name='notify_action_object', 
        on_delete=models.CASCADE,
        blank=True, 
        null=True
    )
    action_object_object_id = models.CharField(max_length=255, blank=True)
    action_object = GenericForeignKey('action_object_content_type', 'action_object_object_id')

    timestamp = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False, db_index=True)
    unread = models.BooleanField(default=True)
    emailed = models.BooleanField(default=False)

    objects = NotificationQuerySet.as_manager()

    def __str__(self):
        ctx = {
            'actor': self.actor,
            'verb': self.verb,
            'action_object': self.action_object,
            'target': self.target,
            'timesince': self.timesince()
        }
        if self.target:
            if self.action_object:
                return u'%(actor)s %(verb)s %(action_object)s on %(target)s %(timesince)s ago' % ctx
            return u'%(actor)s %(verb)s %(target)s %(timesince)s ago' % ctx
        if self.action_object:
            return u'%(actor)s %(verb)s %(action_object)s %(timesince)s ago' % ctx
        return u'%(actor)s %(verb)s %(timesince)s ago' % ctx


    class Meta:
        db_table = 'notifications\".\"notification'
        ordering = ['-timestamp']
        indexes = [
            models.Index(
                fields=['-timestamp'],
                name='notif_timestamp_desc_idx'
            ),
            models.Index(
                # Speed up notifications count query
                fields=['recipient', 'unread'],
                name='notif_recipient_and_unread_idx'
            ),
            models.Index(
                fields=['unread', 'emailed'],
                name='notif_unread_and_emailed_idx'
            )
        ]

