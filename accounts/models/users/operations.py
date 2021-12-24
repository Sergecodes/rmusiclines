"""Contains operations for the various models as mixins"""

from django.db.models import F
from django.utils import timezone

from posts.models.artist_posts.models import (
	ArtistPostDownload,
)
from posts.models.non_artist_posts.models import (
	NonArtistPostDownload
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
		pass

	def unblock_user(self, other):
		pass

	def has_blocked_user(self, other):
		return other in self.blocked_users.all()

	def follow_user(self, other):
		pass

	def unfollow_user(self, other):
		pass

	def add_artist_post(self, post):
		pass

	def add_non_artist_post(self, post):
		pass

	def delete_artist_post(self, post):
		pass

	def delete_non_artist_post(self, post):
		pass

	def add_artist_post_comment(self, post, comment):
		pass

	def add_non_artist_post_comment(self, post, comment):
		pass

	def rate_artist_post(self, post):
		pass

	def rate_non_artist_post(self, post):
		pass

	def remove_artist_post_rating(self, post):
		pass

	def remove_non_artist_post_rating(self, post):
		pass
	
	def download_artist_post(self, post):
		pass

	def download_non_artist_post(self, post):
		pass

	def num_downloads(self, month: int, year: int):
		"""
		Get the number of posts the user downloaded in the given month and year
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
		pass

	def bookmarks_non_artist_post(self, post):
		pass

	def repost_artist_post(self, post, comment=''):
		pass

	def repost_non_artist_post(self, post, comment=''):
		pass

