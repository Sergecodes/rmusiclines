"""Common models are placed here"""

from django.conf.global_settings import LANGUAGES
from django.db import models
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from shortuuid.django_fields import ShortUUIDField
from taggit.models import TagBase

from .operations import PostHashtagOperations


class Post(models.Model):
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
	uuid = ShortUUIDField(
		_('UUID'),
		length=20,
		unique=True,
		max_length=24,
	)
	# The language will be detected via an external language-recognition tool
	language = models.CharField(
		_('Language'),
		choices=LANGUAGES,
		default='en',
		max_length=7
	)
	created_on = models.DateTimeField(
		_('Created on'),
		auto_now_add=True, 
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

	@property
	def num_reposts(self):
		return self.num_simple_reposts + self.num_comment_reposts

	class Meta:
		abstract = True


# See django-taggit docs on how to use a Custom tag
# djanto-taggit.readthedocs.io/en/latest/custom_tagging.html
class PostHashtag(TagBase, PostHashtagOperations):
	# Remember hashtags do not have to contain spaces
	# thus it is sensible to set the name and slug to the same length.
	# As a matter of fact, the name and the slug will always be the same.
	topic = models.CharField(
		verbose_name=pgettext_lazy('Hashtag topic', 'topic'),
		unique=True, 
		max_length=50
	)
	slug = models.SlugField(
		pgettext_lazy('Hashtag slug', 'slug'),
		unique=True,
		max_length=50,
		editable=False
	)

	class Meta:
		verbose_name = _('Post Hashtag')
		verbose_name_plural = _('Post Hashtags')
		db_table = 'posts\".\"post_hashtag'


class PostRepost(models.Model):
	comment = models.TextField(blank=True)
	reposted_on = models.DateTimeField(auto_now_add=True, editable=False)

	class Meta:
		abstract = True


class PostRating(models.Model):
	num_stars = models.PositiveIntegerField(default=0, editable=False)
	rated_on = models.DateTimeField(auto_now_add=True, editable=False)

	class Meta:
		abstract = True


class Comment(models.Model):
	body = models.TextField()
	created_on = models.DateTimeField(auto_now_add=True, editable=False)
	num_likes = models.PositiveIntegerField(default=0, editable=False)
	
	class Meta:
		abstract = True


class CommentLike(models.Model):
	liked_on = models.DateTimeField(auto_now_add=True, editable=False)

	class Meta:
		abstract = True

