import datetime
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from accounts.models.users.models import Suspension
from flagging.models.models import Flag, FlagInstance
from notifications.models.models import Notification
from notifications.signals import notify
from .constants import (
	CONTENT_IS_FLAGGED_COUNT, AUTO_DELETE_FLAGS_COUNT, 
	USER_IS_FLAGGED_COUNT, AUTO_SUSPEND_USER_ACCOUNT_FLAGS_COUNT
)

User = get_user_model()


@receiver(post_save, sender=FlagInstance)
def flagged(sender, instance, created, **kwargs):
	"""Increase flag count in the flag model after creating an instance"""
	if created:    
		flag = instance.flag
		flag.increase_count()
		flag.toggle_flagged_state()

		flag_count, content_object = flag.count, flag.content_object
		object_is_user = isinstance(content_object, User)
		object_has_poster_id = hasattr(content_object, 'poster_id')

		# If a post(comment, post, ...) was flagged
		if object_has_poster_id:
			post = content_object
			poster = post.poster

			# If post is considered FLAGGED,
			# notify user, tell him one of his posts has been flagged
			# notify moderators so they can take desired action; 
			# delete the post or absolve it.
			if flag_count == CONTENT_IS_FLAGGED_COUNT: 
				# Notify poster
				notify.send(
					sender=User.site_services_account,
					recipient=poster, 
					verb=_(
						'Some users reported this content because they found it "inappropriate". '
						"If you think they are wrong, ignore this warning. "
						"Otherwise, please delete this post to prevent your account from being suspended "
						"or it will be deleted. "
						"Also, do avoid posting such content in future. Thanks."
					),
					target=post,
					action_object=instance,
					category=Notification.FLAG,
					level=Notification.WARNING
				)

				# Notify moderators
				notify.send(
					sender=User.site_services_account, 
					recipient=User.moderators, 
					verb=_(
						"This content has been FLAGGED. You can delete it if you find it "
						"inappropriate or absolve it if you find it appropriate."
					),
					target=post,
					action_object=instance,
					category=Notification.REPORTED
				)

			# If post wasn't deleted and number of flags reaches auto deletion threshold,
			# delete post.
			if flag_count == AUTO_DELETE_FLAGS_COUNT:
				# Delete flag object and corresponding post
				flag.delete()
				post.delete()

				# Notify poster that his post has been deleted
				# no `target` here since post has been deleted..
				notify.send(
					sender=User.site_services_account, 
					recipient=poster, 
					verb=_(
						"One of your contents has been deleted because it was considered "
						"inappropriate by many users. Please try to not post such content in the future. Thanks"
					),
					category=Notification.FLAGGED_CONTENT_DELETED
				)

		# If a user account was flagged(by a moderator)
		elif object_is_user:
			flagged_user = content_object
			site_account = User.site_services_account

			# Nofify just poster 
			if flag_count == USER_IS_FLAGGED_COUNT: 
				notify.send(
					sender=site_account,
					recipient=flagged_user, 
					verb=_(
						"We've found some activities on your account that violate our terms of service. "
						"Please stop posting such content, else your account may be deactivated. Thanks"
					),
					target=flagged_user,
					action_object=instance,
					category=Notification.FLAG,
					level=Notification.WARNING
				)

			# Suspend user's account
			if flag_count == AUTO_SUSPEND_USER_ACCOUNT_FLAGS_COUNT:
				Suspension.objects.create(
					suspender=site_account,
					suspended_user=flagged_user,
					duration=datetime.timedelta(days=1),
					reason=_("Account flagged multiple times.")
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
	"""Adjust flag state perhaps after changing CONTENT_IS_FLAGGED_COUNT"""
	for flag in Flag.objects.all():
		flag.toggle_flagged_state()
