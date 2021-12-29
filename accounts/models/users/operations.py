"""Contains operations for the various models as mixins"""

from django.core.exceptions import ValidationError
from django.db.models import F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from posts.models.artist_posts.models import (
	ArtistPostBookmark, ArtistPostDownload,
	ArtistPostRating, ArtistPostRepost,
)
from posts.models.non_artist_posts.models import (
	NonArtistPostBookmark, NonArtistPostDownload,
	NonArtistPostRating, NonArtistPostRepost
)


class UserOperations:
	"""Mixin containing operations to be used on the User model"""

	def deactivate(self):
		"""Mark user as inactive but allow his record in database."""
		# Don't actually delete user account, just do this instead
		self.deactivated_on = timezone.now()
		self.is_active = False
		self.save(update_fields=['is_active', 'deactivated_on'])

	def block_user(self, other):
		from accounts.models.users.models import UserBlocking

		UserBlocking.objects.add(
			blocker=self, 
			blocked=other
		)

	def unblock_user(self, other):
		from accounts.models.users.models import UserBlocking
	
		UserBlocking.objects.delete(
			blocker=self, 
			blocked=other
		)

	def has_blocked_user(self, other):
		"""Return `True` if self has blocked other else `False`"""
		return other in self.blocked_users.all()

	def follow_user(self, other):
		from accounts.models.users.models import UserFollow

		UserFollow.objects.create(
			follower=self,
			followed=other
		)
		self.num_following = F('num_following') + 1
		self.save(update_fields=['num_following'])

		other.num_followers = F('num_followers') + 1
		other.save(update_fields=['num_followers'])

	def unfollow_user(self, other):
		from accounts.models.users.models import UserFollow

		UserFollow.objects.delete(
			follower=self,
			followed=other
		)
		self.num_following = F('num_following') - 1
		self.save(update_fields=['num_following'])

		other.num_followers = F('num_followers') - 1
		other.save(update_fields=['num_followers'])

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
		ArtistPostRating.objects.delete(
			post=post,
			rater=self,
		)

	def remove_non_artist_post_rating(self, post):
		NonArtistPostRating.objects.delete(
			post=post,
			rater=self,
		)
	
	def download_artist_post(self, post):
		ArtistPostDownload.objects.create(
			post=post,
			downloader=self
		)

	def download_non_artist_post(self, post):
		NonArtistPostDownload.objects.create(
			post=post,
			downloader=self
		)

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
		ArtistPostBookmark.objects.delete(
			post=post,
			rater=self,
		)

	def remove_non_artist_post_bookmark(self, post):
		NonArtistPostBookmark.objects.delete(
			post=post,
			rater=self,
		)
	
	def repost_artist_post(self, post, comment=''):
		ArtistPostRepost.objects.create(
			post=post,
			reposter=self,
			comment=comment
		)

	def repost_non_artist_post(self, post, comment=''):
		NonArtistPostRepost.objects.create(
			post=post,
			reposter=self,
			comment=comment
		)

	def delete_artist_post_repost(self, repost_id):
		# Use repost_id since we can't delete by filtering on
		# reposter and post.
		ArtistPostRepost.objects.delete(id=repost_id)

	def delete_artist_post_repost(self, repost_id):
		# Use repost_id since we can't delete by filtering on
		# reposter and post.
		NonArtistPostRepost.objects.delete(id=repost_id)


class SuspensionOperations:
	"""Mixin containing operations to be used on the Suspension model"""

	def end(self):
		if self.is_active:
			raise ValidationError(_('Suspension is still ongoing'))
			
		self.is_active = False
		self.save()


