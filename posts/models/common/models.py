"""Common models are placed here"""

from django.conf.global_settings import LANGUAGES
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from shortuuid.django_fields import ShortUUIDField
from taggit.models import TagBase

from posts.constants import (
	COMMENT_CAN_EDIT_TIME_LIMIT, POST_CAN_EDIT_TIME_LIMIT,
	MAX_COMMENT_LENGTH, MAX_POST_LENGTH
)
from .operations import PostOperations


class Post(models.Model, PostOperations):
	# This will be displayed in the url and will be used rather
	# than the numeric auto-incrementing id.
	# 
	# Since unique=True, django will automatically create an index for this field.
	#
	# A test was made by doing:
	# import shortuuid
	# s, n = shortuuid.ShortUUID(), 1000000  # (1 million uuids)
	# for i in range(10):
	# 	results = [s.random(length=16) for i in range(n)]
	# 	print(len(set(results)) == len(results))
	# 
	# In 10 trials, the set contained the same number of elements as the list,
	# implying that there were no collisions.
	uuid = ShortUUIDField(length=20, unique=True, max_length=24)
	# Max length for post body should be set to 350.
	# Body can be empty in case post contains only media.
	body = models.TextField(blank=True)
	# TODO The language will be detected via an external language-recognition tool
	language = models.CharField(
		_('Language'),
		choices=LANGUAGES,
		default='en',
		max_length=7
	)
	created_on = models.DateTimeField(auto_now_add=True, editable=False)
	last_updated_on = models.DateTimeField(auto_now=True, editable=False)
	is_private = models.BooleanField(default=False)
	# Is post a normal repost(repost without body)? If it is null, then post is a 
	# parent(post is not a repost)
	is_simple_repost = models.BooleanField(null=True, blank=True)
	num_ancestor_comments = models.PositiveIntegerField(
		_('Number of ancestor comments'),
		default=0,
		editable=False
	)
	num_stars = models.PositiveIntegerField(
		_('Number of stars'),
		default=0, 
		editable=False
	)
	num_bookmarks = models.PositiveIntegerField(
		_('Number of bookmarks'),
		default=0, 
		editable=False
	)
	num_views = models.PositiveIntegerField(
		_('Number of views'),
		default=0, 
		editable=False
	)
	num_downloads = models.PositiveIntegerField(
		_('Number of downloads'),
		default=0, 
		editable=False
	)
	num_simple_reposts = models.PositiveIntegerField(
		_('Number of reposts without body'),
		default=0, 
		editable=False
	)
	num_non_simple_reposts = models.PositiveIntegerField(
		_('Number of reposts with body'),
		default=0, 
		editable=False
	)

	def __str__(self):
		return self.body

	@property
	def is_parent(self):
		return self.is_simple_repost is None

	@property
	def is_repost(self):
		return not self.is_parent

	# @property
	# def ancestor(self):
	# 	"""Get ancestor post. This will fail if parent post has been deleted."""
	# 	ancestor, parent = None, self.parent
	# 	while parent is not None:
	# 		ancestor = parent
	# 		parent = parent.parent

	# 	return ancestor

	@property
	def ancestor_comments(self):
		"""Get comments that are comments to post(ancestors) and not replies"""
		return self.overall_comments.filter(ancestor__isnull=True)

	@property
	def simple_reposts(self):
		"""Get reposts that don't have a body(that are just reposts)"""
		return self.reposts.filter(is_simple_repost=True)

	@property
	def non_simple_reposts(self):
		"""Get reposts that have a body(that are not just reposts)"""
		return self.reposts.filter(is_simple_repost=False)

	@property
	def num_reposts(self):
		return self.num_simple_reposts + self.num_non_simple_reposts
	
	@property
	def can_be_edited(self):
		"""Verify if post is within edit time frame"""
		if timezone.now() - self.created_on > POST_CAN_EDIT_TIME_LIMIT:
			return False
		return True

	@property
	def has_been_edited(self):
		"""Returns whether a post has been edited after its creation or not"""
		return self.created_on != self.last_updated_on
	
	@property
	def get_tags(self):
		"""Return list of hashtags. Used in the graphql api to get tags of a post."""
		return list(self.hashtags.all())

	def clean(self):
		# Validate post length
		if len(self.body) > MAX_POST_LENGTH:
			raise ValidationError(
				_('Post should have at most %(max_post_length)s characters.'),
				code='invalid',
				params={'max_post_length': MAX_POST_LENGTH}
			)

		# Ensure pinned comment is an ancestor comment
		pinned_comment = self.pinned_comment
		if pinned_comment and not pinned_comment.is_ancestor:
			raise ValidationError(
				_('You can only pin an ancestor comment'),
				code='not_ancestor_comment'
			)

	def save(self, *args, **kwargs):
		self.clean()
		super().save(*args, **kwargs)

	class Meta:
		abstract = True


# See django-taggit docs on how to use a Custom tag
# djanto-taggit.readthedocs.io/en/latest/custom_tagging.html
class PostHashtag(TagBase):
	# Remember hashtags do not have to contain spaces
	# thus it is sensible to set the name and slug to the same length.
	# As a matter of fact, the name and the slug will always be the same.
	#
	# However, unicode characters might be different 
	# (eg. chinese slugs might turn out to be longer); so just 
	# set the slug to a bigger max_length
	name = models.CharField(
        verbose_name=pgettext_lazy("Hashtag name", "name"), 
		unique=True, 
		max_length=40
    )
	slug = models.SlugField(
		pgettext_lazy('Hashtag slug', 'slug'),
		unique=True,
		max_length=100,
		allow_unicode=True
	)

	@property
	def artist_posts(self):
		from posts.models.artist_posts.models import ArtistPost

		return ArtistPost.objects.filter(hashtags__in=[self]).distinct()

	@property
	def non_artist_posts(self):
		from posts.models.non_artist_posts.models import NonArtistPost

		return NonArtistPost.objects.filter(hashtags__in=[self]).distinct()

	def clean(self):
		hashtag = self.name

		# `isalpha()` validates even unicode characters
		if not hashtag.isalpha():
			raise ValidationError(
				_("Hashtags should be alphabetic(can not contain symbols nor whitespace)"),
				code='invalid'
			)
		
	def save(self, *args, **kwargs):
		self.clean()
		super().save(*args, **kwargs)

	class Meta:
		verbose_name = _('Post Hashtag')
		verbose_name_plural = _('Post Hashtags')
		db_table = 'posts\".\"post_hashtag'
		constraints = [
			models.CheckConstraint(
				# Hashtag should be alphabetic
				# See https://postgresql.org/docs/current/functions-matching.html
				# (bracket expressions)
				check=Q(name__regex=r'^[[:alpha:]]+$'),
				name='hashtag_is_alphabetic'
			)
		]


class PostRating(models.Model):
	num_stars = models.PositiveIntegerField(editable=False)
	rated_on = models.DateTimeField(auto_now_add=True, editable=False)

	def clean(self):
		valid_stars = (1, 3, 5)

		if self.num_stars not in valid_stars:
			raise ValidationError(
				_('Invalid rating, rating must have 1, 3 or 5 stars'),
				code='invalid'
			)

	def save(self, *args, **kwargs):
		self.clean()
		super().save(*args, **kwargs)

	class Meta:
		abstract = True


class Comment(models.Model):
	uuid = ShortUUIDField(length=16, unique=True, max_length=24)
	body = models.TextField()
	last_updated_on = models.DateTimeField(auto_now=True, editable=False)
	created_on = models.DateTimeField(auto_now_add=True, editable=False)
	num_likes = models.PositiveIntegerField(default=0, editable=False)
	# If comment is an ancestor, this will hold its number of child comments(its number
	# of descendant comments - by default 0). Else it will be null
	num_child_comments = models.PositiveIntegerField(blank=True, null=True, editable=False)
	num_replies = models.PositiveIntegerField(default=0, editable=False)
	
	def __str__(self):
		return self.body

	@property
	def is_ancestor(self):
		"""Is the comment a direct comment on the post or a sub comment"""
		return True if self.ancestor is None else False

	@property
	def is_child_comment(self):
		"""Verify if comment is a reply to another comment(if comment is a sub comment)"""
		return not self.is_ancestor

	@property
	def is_reply_to_an_ancestor(self):
		"""Is the comment a reply to an ancestor comment"""
		return not self.is_ancestor and self.ancestor == self.parent

	@property
	def can_be_edited(self):
		"""Verify if comment is within edit time frame"""
		if timezone.now() - self.created_on > COMMENT_CAN_EDIT_TIME_LIMIT:
			return False
		return True

	def clean(self):
		# Max length of comment body should be 1000 chars; 
		# we don't want the user to abuse an unlimited field.
		if len(self.body) > MAX_COMMENT_LENGTH:
			raise ValidationError(
				_('Comments should be less than %(max_length)s characters'),
				code='max_length',
				params={'max_length': MAX_COMMENT_LENGTH}
			)
	
	def save(self, *args, **kwargs):
		self.clean()
		super().save(*args, **kwargs)
	
	class Meta:
		abstract = True


class CommentLike(models.Model):
	liked_on = models.DateTimeField(auto_now_add=True, editable=False)

	class Meta:
		abstract = True

