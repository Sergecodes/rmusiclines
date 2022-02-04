"""Contains operations for the various models as mixins"""

from actstream.actions import follow, unfollow
from django.core.exceptions import ValidationError
from django.db.models import F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.constants import USERNAME_CHANGE_WAIT_PERIOD
from accounts.models.artists.models import ArtistFollow
from flagging.models.models import Flag
from posts.models.artist_posts.models import (
	ArtistPostBookmark, ArtistPostDownload,
	ArtistPostRating, 
)
from posts.models.non_artist_posts.models import (
	NonArtistPostBookmark, NonArtistPostDownload,
	NonArtistPostRating,
)


class UserOperations:
	"""Mixin containing operations to be used on the User model"""

	def deactivate(self):
		"""Mark user as inactive but allow his record in database."""
		# Don't actually delete user account, just do this instead
		self.deactivated_on = timezone.now()
		self.is_active = False
		self.save(update_fields=['is_active', 'deactivated_on'])

		# Update graphql_auth status
		self.status.verified = False
		self.status.save(update_fields=['verified'])

	def change_username(self, new_username: str):
		"""
		Change a user's username. This method should be used to modify
		a user's username rather than directly calling save().
		"""
		if not self.can_change_username:
			raise ValidationError(
				_(
					"You cannot change your username until the %(can_change_date)s; "
					"you need to wait %(wait_period)s days after changing your username."
				),
				code="can't_change_username_yet",
				params={
					'can_change_date': str(self.can_change_username_until_date),
					'wait_period': USERNAME_CHANGE_WAIT_PERIOD
				}
			)

		if self.username == new_username:
			raise ValidationError(
				_("This is your current username"),
				code="same_username"
			)

		self.username = new_username
		self.last_changed_username_on = timezone.now()
		self.save(update_fields=['username', 'last_changed_username_on'])

	def absolve_content(self, content):
		"""
		Resolve the flag of a content. This content should use the FlagMixin.
		User should be a moderator.
		"""
		if not self.is_mod:
			raise ValidationError(
				_('Only moderators can absolve content'),
				code="can't_absolve_content"
			)

		flag = content.flag
		flag.toggle_state(Flag.State.RESOLVED, self)

	def follow_artist(self, artist):
		ArtistFollow.objects.create(follower=self, artist=artist)

		# Add action
		follow(self, artist)

		artist.num_followers = F('num_followers') + 1
		artist.save(update_fields=['num_followers'])

	def unfollow_artist(self, artist):
		ArtistFollow.objects.get(follower=self, artist=artist).delete()

		# Remove action
		unfollow(self, artist)

		artist.num_followers = F('num_followers') - 1
		artist.save(update_fields=['num_followers'])


	def block_user(self, other):
		from accounts.models.users.models import UserBlocking

		UserBlocking.objects.create(blocker=self, blocked=other)

	def unblock_user(self, other):
		from accounts.models.users.models import UserBlocking

		UserBlocking.objects.get(blocker=self, blocked=other).delete()

	def has_blocked_user(self, other):
		"""Return `True` if self has blocked other else `False`"""
		return other in self.blocked_users.all()

	def follow_user(self, other):
		from accounts.models.users.models import UserFollow

		UserFollow.objects.create(
			follower=self,
			followed=other
		)

		# Add action
		follow(self, other)

		self.num_following = F('num_following') + 1
		self.save(update_fields=['num_following'])

		other.num_followers = F('num_followers') + 1
		other.save(update_fields=['num_followers'])

	def unfollow_user(self, other):
		from accounts.models.users.models import UserFollow

		UserFollow.objects.get(follower=self, followed=other).delete()

		# Remove action
		unfollow(self, other)
		
		self.num_following = F('num_following') - 1
		self.save(update_fields=['num_following'])

		other.num_followers = F('num_followers') - 1
		other.save(update_fields=['num_followers'])

	## Most of these methods have signals attached that 
	# add or reduce the corresponding attribute count.

	def rate_artist_post(self, post, num_stars):
		"""
		`post`: Artist Post
		`num_stars`: Number of stars between 1 and 5 (inclusive)
		"""
		ArtistPostRating.objects.create(
			post=post,
			rater=self,
			num_stars=num_stars
		)

	def rate_non_artist_post(self, post, num_stars):
		"""
		`post`: Non Artist Post
		`num_stars`: Number of stars between 1 and 5 (inclusive)
		"""
		NonArtistPostRating.objects.create(
			post=post,
			rater=self,
			num_stars=num_stars
		)

	def remove_artist_post_rating(self, post):
		ArtistPostRating.objects.get(post=post, rater=self).delete()

	def remove_non_artist_post_rating(self, post):
		NonArtistPostRating.objects.get(post=post, rater=self).delete()
	
	def download_artist_post(self, post):
		ArtistPostDownload.objects.create(post=post, downloader=self)

	def download_non_artist_post(self, post):
		NonArtistPostDownload.objects.create(post=post, downloader=self)

	def num_downloads(self, month: int, year: int):
		"""
		Get the number of posts the user downloaded in the `month` month of the year `year`.
		"""
		return ArtistPostDownload.objects.filter(
			downloader=self,
			downloaded_on__month=month,
			downloaded_on__year=year
		).count() + NonArtistPostDownload.objects.filter(
			downloader=self,
			downloaded_on__month=month,
			downloaded_on__year=year
		).count()

	def bookmark_artist_post(self, post):
		ArtistPostBookmark.objects.create(
			post=post,
			bookmarker=self
		)

	def bookmark_non_artist_post(self, post):
		NonArtistPostBookmark.objects.create(
			post=post,
			bookmarker=self
		)
	
	def remove_artist_post_bookmark(self, post):
		ArtistPostBookmark.objects.get(post=post, rater=self).delete()

	def remove_non_artist_post_bookmark(self, post):
		NonArtistPostBookmark.objects.get(post=post, rater=self).delete()
	
	def repost_artist_post(self, post, comment=''):
		pass

	def repost_non_artist_post(self, post, comment=''):
		pass

	def delete_artist_post_repost(self, repost_id):
		# Use repost_id since we can't delete by filtering on
		# reposter and post.
		pass

	def delete_artist_post_repost(self, repost_id):
		pass


class SuspensionOperations:
	"""Mixin containing operations to be used on the Suspension model"""

	def end(self):
		if self.is_active:
			raise ValidationError(
				_('Suspension is still ongoing'),
				code='ongoing_suspension'
			)
			
		# Mark suspension as no longer active
		self.is_active = False
		self.save(update_fields=['is_active'])


