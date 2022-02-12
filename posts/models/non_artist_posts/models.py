from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.fields import ThumbnailerImageField
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

from core.constants import FILE_STORAGE_CLASS
from core.fields import DynamicStorageFileField
from core.mixins import UsesCustomSignal
from flagging.mixins import FlagMixin
from posts.constants import (
	ARTIST_POSTS_VIDEOS_UPLOAD_DIR, 
	NON_ARTIST_POSTS_PHOTOS_UPLOAD_DIR
)
from posts.validators import validate_post_photo_file, validate_post_video_file
from .operations import NonArtistPostOperations
from ..common.models import (
    Post, PostHashtag, PostRating, 
	Comment, CommentLike
)


class NonArtistPost(Post, NonArtistPostOperations, FlagMixin, UsesCustomSignal):
	hashtags = TaggableManager(
		verbose_name=_('Hashtags'), 
		through='HashtaggedNonArtistPost',
		blank=True
	)
	parent = models.ForeignKey(
		'self',
		on_delete=models.SET_NULL,
		related_name='reposts',
		related_query_name='repost',
		db_column='parent_post_id',
		null=True,
		blank=True
	)
	poster = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='non_artist_posts',
		related_query_name='non_artist_post',
		db_column='user_id'
	)
	pinned_comment = models.OneToOneField(
		'NonArtistPostComment',
		db_column='pinned_comment_id',
		related_name='+',
		on_delete=models.CASCADE,
		blank=True,
		null=True
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

	def clean(self):
		super().clean()

	def save(self, *args, **kwargs):
		self.clean()
		super().save(*args, **kwargs)

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
	photo = ThumbnailerImageField(
		thumbnail_storage=FILE_STORAGE_CLASS(), 
		upload_to=NON_ARTIST_POSTS_PHOTOS_UPLOAD_DIR,
		resize_source=dict(size=(1000, 1000), sharpen=True),
		validators=[
			FileExtensionValidator(['png, jpg, gif']), 
			validate_post_photo_file
		],
		width_field='photo_width', 
		height_field='photo_height'
	)
	photo_width = models.PositiveIntegerField()
	photo_height = models.PositiveIntegerField()

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
	video = DynamicStorageFileField(
		upload_to=ARTIST_POSTS_VIDEOS_UPLOAD_DIR, 
		validators=[
			FileExtensionValidator(['mp4', 'mov']), 
			validate_post_video_file
		],
		blank=True
	)

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
		related_name='hashtagged_hashtags',
		related_query_name='hashtagged_hashtag'
	)
	# django-taggit says the name `tag` must be used
	# Check out the parent class to see how they implemented this field (tag)
	tag = models.ForeignKey(
		PostHashtag,
		on_delete=models.CASCADE,
		db_column='post_hashtag_id',
		related_name='hashtagged_non_artist_posts',
		# Don't set related_query_name. Just allow it.
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


class NonArtistPostRating(PostRating):
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
		return f'Post {str(self.post)} rated {self.num_stars} star(s) by {str(self.rater)}'
	
	class Meta:
		db_table = 'posts\".\"non_artist_post_rating'
		constraints = [
			models.UniqueConstraint(
				fields=['post', 'rater'],
				name='unique_non_artist_post_rating'
			),
			models.CheckConstraint(
				check=Q(num_stars=1) | Q(num_stars=3) | Q(num_stars=5),
				name='non_artist_post_rating_stars_is_1_or_3_or_5'
			)
		]


class NonArtistPostBookmark(models.Model):
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


class NonArtistPostComment(Comment, FlagMixin, UsesCustomSignal):
	parent = models.ForeignKey(
		'self',
		on_delete=models.SET_NULL,
		related_name='replies',
		related_query_name='reply',
		db_column='parent_comment_id',
		# Is nullable since comment can be direct comment on post 
		# hence it doesn't have a parent comment or its parent is deleted;
		# like in youtube comments, when a sub comment is deleted, its replies are
		# not deleted
		blank=True,
		null=True
	)
	# Ancestor comment is direct comment on post
	ancestor = models.ForeignKey(
		'self',
		on_delete=models.CASCADE,
		related_name='child_comments',
		related_query_name='child_comment',
		db_column='ancestor_comment_id',
		# Is nullable since comment can be direct comment on post 
		# hence it doesn't have an ancestor comment
		blank=True,
		null=True
	)
	poster = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		db_column='user_id',
		on_delete=models.CASCADE,
		related_name='overall_non_artist_post_comments',
		related_query_name='non_artist_post_comment'
	)
	# Post on which comment was made
	post_concerned = models.ForeignKey(
		NonArtistPost,
		db_column='non_artist_post_concerned_id',
		on_delete=models.CASCADE,
		related_name='overall_comments',
		related_query_name='comment'
	)
	likers = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		through='NonArtistPostCommentLike',
		related_name='liked_non_artist_post_comments',
		related_query_name='liked_non_artist_post_comment'
	)
	users_mentioned = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		through='NonArtistPostCommentMention',
		related_name='mentioned_in_non_artist_post_comment',
		related_query_name='mentioned_in_non_artist_post_comment',
		blank=True
	)

	class Meta: 
		db_table = 'posts\".\"non_artist_post_comment'
		ordering = ['-num_likes', '-created_on', '-num_child_comments']


class NonArtistPostCommentLike(CommentLike):
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


class NonArtistPostCommentMention(models.Model):
	"""Non artist post comment and user mention through model"""

	comment = models.ForeignKey(
		NonArtistPostComment,
		db_column='non_artist_post_comment_id',
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
		return f'Comment {str(self.comment)} mentions {str(self.user_mentioned)}'

	class Meta:
		db_table = 'posts\".\"non_artist_post_comment_user_mention'
		constraints = [
			models.UniqueConstraint(
				fields=['comment', 'user_mentioned'],
				name='unique_non_artist_post_comment_user_mention'
			),
		]

