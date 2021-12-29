from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from flagging.models.models import Flag, FlagInstance
from notifications.models.models import Notification
from notifications.signals import notify
from .constants import IS_FLAGGED_COUNT

User = get_user_model()


@receiver(post_save, sender=FlagInstance)
def flagged(sender, instance, created, **kwargs):
	"""Increase flag count in the flag model after creating an instance"""
	if created:    
		flag = instance.flag
		flag.increase_count()
		flag.toggle_flagged_state()

		count, post = flag.count, flag.content_object
		poster = post.poster
		# if post is considered FLAGGED,
		# notify user, tell him one of his posts has been flagged
		# notify moderators so they can take desired action; 
		# delete the post or absolve it.
		if count == IS_FLAGGED_COUNT: 
			notify.send(
				sender=poster,  # just use same user as sender
				recipient=poster, 
				verb=_(
					"Some users considered this post inappropriate. "
					"Edit or delete it now to prevent suspension. "
					"Also, ensure to avoid posting such posts in future."
				),
				target=post,
				category=Notification.FLAG
			)

			for moderator in User.moderators.all():
				notify.send(
					sender=moderator,  # just use moderator as sender
					recipient=moderator, 
					verb=_(
						"This post has been FLAGGED. You can delete it if you find it "
						"inappropriate or absolve if you find it appropriate."
					),
					target=post,
					category=Notification.REPORTED
				)

			return

		# if for some reason, post is still on site and has not yet been deleted by moderators
		# and it is DOUBLY FLAGGED; delete it and notify poster.
		# just use 2*IS_FLAGGED_COUNT so that user can have some time to edit post...
		# and moderator can have small time(time for another user to add a flag) to review post. 
		if count == 2 * IS_FLAGGED_COUNT:
			pass

		# if for some reason at this point post is stilll on site, delete post.
		# and notify user
		if count > 2 * IS_FLAGGED_COUNT:
			post.delete()
			# Notify poster that his post has been deleted
			# no `target` here since post has been deleted..
			notify.send(
				sender=poster,  # just use same user as sender
				recipient=poster, 
				verb=_(
					"One of your posts has been deleted because it was considered "
					"inappropriate by many users."
				),
				category=Notification.FLAG
			)


@receiver(post_delete, sender=FlagInstance)
def unflagged(sender, instance, **kwargs):
	"""Decrease flag count in the flag model after deleting an instance"""
	flag = instance.flag
	flag.decrease_count()
	flag.toggle_flagged_state()


# The following signals are registered in flagging.__init__'s ready method.
def create_permission_groups(sender, **kwargs):
	"""Create permissions related to flagging."""
	flag_ct = ContentType.objects.get_for_model(Flag)
	delete_flagged_perm, __ = Permission.objects.get_or_create(
		codename='delete_flagged_content',
		name=_('Can delete flagged content'),
		content_type=flag_ct
	)
	moderator_group, __ = Group.objects.get_or_create(name='flag_moderator')
	moderator_group.permissions.add(delete_flagged_perm)


def adjust_flagged_content(sender, **kwargs):
	"""Adjust flag state perhaps after changing FLAGS_ALLOWED count"""
	for flag in Flag.objects.all():
		flag.toggle_flagged_state()
