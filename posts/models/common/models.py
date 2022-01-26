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
	COMMENT_CAN_EDIT_TIME_LIMIT, 
	POST_CAN_EDIT_TIME_LIMIT,
	MAX_POST_LENGTH
)
from .operations import PostOperations, PostHashtagOperations


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
	# Max length for this field should be set to 350.
	body = models.TextField(blank=True)
	# The language will be detected via an external language-recognition tool
	language = models.CharField(
		_('Language'),
		choices=LANGUAGES,
		default='en',
		max_length=7
	)
	created_on = models.DateTimeField(auto_now_add=True, editable=False)
	last_updated_on = models.DateTimeField(auto_now=True, editable=False)
	is_private = models.BooleanField(default=False)
	num_parent_comments = models.PositiveIntegerField(
		_('Number of parent comments'),
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
		_('Number of reposts without a comment'),
		default=0, 
		editable=False
	)
	num_comment_reposts = models.PositiveIntegerField(
		_('Number of reposts with a comment'),
		default=0, 
		editable=False
	)

	def __str__(self):
		return self.body

	@property
	def num_reposts(self):
		return self.num_simple_reposts + self.num_comment_reposts
	
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

	def clean(self):
		if len(self.body) > MAX_POST_LENGTH:
			raise ValidationError(
				_('Post should have at most {} characters.'.format(MAX_POST_LENGTH)),
				code='invalid'
			)

	def save(self, *args, **kwargs):
		self.clean()
		super().save(*args, **kwargs)

	class Meta:
		abstract = True


# See django-taggit docs on how to use a Custom tag
# djanto-taggit.readthedocs.io/en/latest/custom_tagging.html
class PostHashtag(TagBase, PostHashtagOperations):
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


class PostRepost(models.Model):
	comment = models.TextField(blank=True)
	reposted_on = models.DateTimeField(auto_now_add=True, editable=False)

	class Meta:
		abstract = True


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
	num_replies = models.PositiveIntegerField(default=0, editable=False)
	# Is the comment an actual comment on the post or a reply to another comment
	is_parent = models.BooleanField(default=True)
	
	def __str__(self):
		return self.body

	@property
	def can_be_edited(self):
		"""Verify if comment is within edit time frame"""
		if timezone.now() - self.created_on > COMMENT_CAN_EDIT_TIME_LIMIT:
			return False
		return True

	@property
	def is_reply(self):
		"""Verify if comment is a reply to another comment"""
		return not self.is_parent
	
	class Meta:
		abstract = True


class CommentLike(models.Model):
	liked_on = models.DateTimeField(auto_now_add=True, editable=False)

	class Meta:
		abstract = True

