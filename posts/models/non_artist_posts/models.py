from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

from core.utils import UsesCustomSignal
from .operations import NonArtistPostOperations
from ..common.models import (
    Post, PostHashtag, 
    PostRating, PostRepost,
    Comment, CommentLike
)


class NonArtistPost(Post, NonArtistPostOperations, UsesCustomSignal):
	hashtags = TaggableManager(
		verbose_name=_('Hashtags'), 
		through='HashtaggedNonArtistPost',
		related_name='non_artist_posts',
		blank=True
	)
	poster = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='non_artist_posts',
		related_query_name='non_artist_post',
		db_column='user_id'
	)
	users_mentioned = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		through='NonArtistPostMention',
		related_name='mentioned_in_non_artist_posts',
		related_query_name='mentioned_in_non_artist_post',
		blank=True
	)
	raters = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		through='NonArtistPostRating',
		related_name='rated_non_artist_posts',
		related_query_name='rated_non_artist_post',
		blank=True
	)
	reposters = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		through='NonArtistPostRepost',
		related_name='reposted_non_artist_posts',
		related_query_name='reposted_non_artist_post',
		blank=True
	)
	bookmarkers = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		through='NonArtistPostBookmark',
		related_name='bookmarked_non_artist_posts',
		related_query_name='bookmarked_non_artist_post',
		blank=True
	)
	downloaders = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		through='NonArtistPostDownload',
		related_name='downloaded_non_artist_posts',
		related_query_name='downloaded_non_artist_post',
		blank=True
	)

	class Meta:
		db_table = 'posts\".\"non_artist_post'
		ordering = ['-created_on']
		indexes = [
			models.Index(
				fields=['-created_on'], 
				name='non_artist_post_desc_idx'
			)
		]

	
class NonArtistPostPhoto(models.Model):
	post = models.ForeignKey(
		NonArtistPost,
		verbose_name=_('Post'),
		db_column='non_artist_post_id',
		on_delete=models.CASCADE,
		related_name='photos',
		related_query_name='photo'
	)
	photo = models.ImageField(
		_('Photo'),
		width_field='photo_width', 
		height_field='photo_height'
	)
	photo_width = models.PositiveIntegerField(_('Photo width'))
	photo_height = models.PositiveIntegerField(_('Photo height'))

	def __str__(self):
		return f'Post {str(self.post)} photo'

	class Meta:
		db_table = 'posts\".\"non_artist_post_photo'


class NonArtistPostVideo(models.Model):
	post = models.OneToOneField(
		NonArtistPost,
		db_column='non_artist_post_id',
		on_delete=models.CASCADE,
		related_name='video',
		related_query_name='video'
	)
	video = models.FileField()

	def __str__(self):
		return f'Post {str(self.post)} video'

	class Meta:
		db_table = 'posts\".\"non_artist_post_video'


class HashtaggedNonArtistPost(TaggedItemBase):
	"""Hashtag and NonArtistPost through model"""

	# DON'T rename this field !!
	# django-taggit says the name `content_object` must be used
	content_object = models.ForeignKey(
		NonArtistPost,
		on_delete=models.CASCADE,
		db_column='non_artist_post_id',
		related_name='+'
	)
	# django-taggit says the name `tag` must be used
	# Check out the parent class to see how they implemented this field (tag)
	tag = models.ForeignKey(
		PostHashtag,
		on_delete=models.CASCADE,
		db_column='post_hashtag_id',
		related_name='+'
	)

	class Meta:
		db_table = 'posts\".\"non_artist_post_with_hashtag'


class NonArtistPostMention(models.Model):
	"""Non artist post and user mention through model"""

	post = models.ForeignKey(
		NonArtistPost,
		db_column='non_artist_post_id',
		on_delete=models.CASCADE,
		related_name='+'
	)
	user_mentioned = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		db_column='user_id',
		on_delete=models.CASCADE,
		related_name='+'
	)

	def __str__(self):
		return f'Post {str(self.post)} mentions {str(self.user_mentioned)}'

	@property
	def mentioned_on(self):
		# A user is mentioned only when a post is created since
		# a posts can't be edited
		return self.post.created_on

	class Meta:
		db_table = 'posts\".\"non_artist_post_user_mention'
		constraints = [
			models.UniqueConstraint(
				fields=['post', 'user_mentioned'],
				name='unique_non_artist_post_user_mention'
			),
		]


class NonArtistPostRepost(PostRepost, UsesCustomSignal):
	"""Non artist post and reposter through model"""

	post = models.ForeignKey(
		NonArtistPost,
		db_column='non_artist_post_id',
		on_delete=models.CASCADE,
		related_name='reposts',
		related_query_name='repost',
	)
	reposter = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		db_column='user_id',
		on_delete=models.CASCADE,
		related_name='non_artist_post_reposts',
		related_query_name='non_artist_post_repost',
	)

	def __str__(self):
		return f'Post {str(self.post)} reposted by {str(self.reposter)}'

	class Meta:
		db_table = 'posts\".\"non_artist_post_repost'
		ordering = ['-reposted_on']
		constraints = [
			models.UniqueConstraint(
				fields=['post', 'reposter'],
				name='unique_non_artist_post_repost'
			),
		]


class NonArtistPostRating(PostRating, UsesCustomSignal):
	"""Non artist post and rater through model"""

	post = models.ForeignKey(
		NonArtistPost,
		db_column='non_artist_post_id',
		on_delete=models.CASCADE,
		related_name='ratings',
		related_query_name='rating',
	)
	rater = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		db_column='user_id',
		on_delete=models.CASCADE,
		related_name='non_artist_post_ratings',
		related_query_name='non_artist_post_rating',
	)

	def __str__(self):
		return f'Post {str(self.post)} rated {self.num_stars} star(s) by {str(self.reposter)}'
	
	class Meta:
		db_table = 'posts\".\"non_artist_post_rating'
		constraints = [
			models.UniqueConstraint(
				fields=['post', 'rater'],
				name='unique_non_artist_post_rating'
			),
			models.CheckConstraint(
				check=Q(num_stars__gte=1) & Q(num_stars__lte=5),
				name='non_artist_post_rating_stars_betw_1_and_5'
			)
		]


class NonArtistPostBookmark(models.Model, UsesCustomSignal):
	"""Non artist post and bookmarker through model"""

	post = models.ForeignKey(
		NonArtistPost,
		db_column='non_artist_post_id',
		on_delete=models.CASCADE,
		related_name='+'
	)
	bookmarker = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		db_column='user_id',
		on_delete=models.CASCADE,
		related_name='+'
	)
	bookmarked_on = models.DateTimeField(auto_now_add=True, editable=False)

	def __str__(self):
		return f'Post {str(self.post)} bookmarked by {str(self.bookmarker)}'
	
	class Meta:
		db_table = 'posts\".\"non_artist_post_bookmark'
		constraints = [
			models.UniqueConstraint(
				fields=['post', 'bookmarker'],
				name='unique_non_artist_post_bookmark'
			),
		]

class NonArtistPostDownload(models.Model):
	"""Non artist post and downloader through model"""

	post = models.ForeignKey(
		NonArtistPost,
		db_column='non_artist_post_id',
		on_delete=models.CASCADE,
		related_name='+'
	)
	downloader = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		db_column='user_id',
		on_delete=models.CASCADE,
		related_name='non_artist_post_downloads',
		related_query_name='non_artist_post_download'
	)
	downloaded_on = models.DateTimeField(auto_now_add=True, editable=False)

	def __str__(self):
		return f'Post {str(self.post)} downloaded by {str(self.downloader)}'
	
	class Meta:
		db_table = 'posts\".\"non_artist_post_download'


class NonArtistPostComment(Comment, UsesCustomSignal):
	parent = models.ForeignKey(
		'self',
		on_delete=models.CASCADE,
		related_name='replies',
		related_query_name='reply',
		db_column='parent_comment_id',
		blank=True,
		null=True
	)
	poster = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		db_column='user_id',
		on_delete=models.CASCADE,
		related_name='non_artist_post_comments',
		related_query_name='non_artist_post_comment'
	)
	post = models.ForeignKey(
		NonArtistPost,
		db_column='non_artist_post_id',
		on_delete=models.CASCADE,
		related_name='comments',
		related_query_name='comment'
	)
	likers = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		through='NonArtistPostCommentLike',
		related_name='liked_non_artist_post_comments',
		related_query_name='liked_non_artist_post_comment'
	)

	@property
	def is_parent(self):
		return True if self.parent is None else False

	class Meta: 
		db_table = 'posts\".\"non_artist_post_comment'
		ordering = ['-num_likes', '-created_on']


class NonArtistPostCommentLike(CommentLike, UsesCustomSignal):
	comment = models.ForeignKey(
		NonArtistPostComment,
		db_column='non_artist_post_comment_id',
		on_delete=models.CASCADE,
		related_name='+'
	)
	liker = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		db_column='user_id',
		on_delete=models.CASCADE,
		related_name='+'
	)

	def __str__(self):
		return f'Comment {str(self.comment)} liked by {str(self.liker)}'

	class Meta:
		db_table = 'posts\".\"non_artist_post_comment_like'
		constraints = [
			models.UniqueConstraint(
				fields=['comment', 'liker'],
				name='unique_non_artist_post_comment_like'
			),
		]


