from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.fields import ThumbnailerImageField
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

from accounts.models.artists.models import Artist
from core.constants import FILE_STORAGE_CLASS
from core.fields import DynamicStorageFileField
from core.mixins import UsesCustomSignal
from flagging.mixins import FlagMixin
from posts.constants import ARTIST_POST_PHOTO_UPLOAD_DIR, ARTIST_POST_VIDEO_UPLOAD_DIR
from posts.managers import ArtistPostRepostManager, ArtistParentPostManager
from posts.mixins import PostMediaMixin
from posts.validators import validate_post_photo_file, validate_post_video_file
from .operations import ArtistPostOperations
from ..common.models import Post, PostHashtag, PostRating, Comment, CommentLike


def artist_post_photo_upload_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/users/user_<id>/artist_posts_photos/<filename>
    return 'users/user_{0}/{1}/{2}'.format(
		instance.post.poster_id, 
		ARTIST_POST_PHOTO_UPLOAD_DIR,
		filename
	)


def artist_post_video_upload_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/user_<id>/artist_posts_videos/<filename>
    return 'users/user_{0}/{1}/{2}'.format(
		instance.post.poster_id, 
		ARTIST_POST_VIDEO_UPLOAD_DIR,
		filename
	)


class ArtistPost(Post, ArtistPostOperations, FlagMixin, UsesCustomSignal):
	hashtags = TaggableManager(
		verbose_name=_('Hashtags'), 
		through='HashtaggedArtistPost',
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
		verbose_name=_('Poster'),
		on_delete=models.CASCADE,
		related_name='artist_posts',
		related_query_name='artist_post',
		db_column='user_id'
	)
	artist = models.ForeignKey(
		Artist,
		verbose_name=_('Artist'),
		on_delete=models.CASCADE,
		related_name='posts',
		related_query_name='post',
		db_column='artist_id'
	)
	pinned_comment = models.OneToOneField(
		'ArtistPostComment',
		db_column='pinned_comment_id',
		related_name='+',
		on_delete=models.CASCADE,
		blank=True,
		null=True
	)
	users_mentioned = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		verbose_name=_('Users mentioned'),
		through='ArtistPostMention',
		related_name='mentioned_in_artist_posts',
		related_query_name='mentioned_in_artist_post',
		blank=True
	)
	raters = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		verbose_name=_('Raters'),
		through='ArtistPostRating',
		related_name='rated_artist_posts',
		related_query_name='rated_artist_post',
		blank=True
	)
	bookmarkers = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		verbose_name=_('Bookmarkers'),
		through='ArtistPostBookmark',
		related_name='bookmarked_artist_posts',
		related_query_name='bookmarked_artist_post',
		blank=True
	)
	downloaders = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		verbose_name=_('Downloaders'),
		through='ArtistPostDownload',
		related_name='downloaded_artist_posts',
		related_query_name='downloaded_artist_post',
		blank=True
	)

	def clean(self):
		super().clean()

		# Ensure post and parent concern the same artist
		if self.parent and self.parent.artist_id != self.artist_id:
			raise ValidationError(
				_('An artist post repost must be of the same artist as the parent post'),
				code='invalid'
			)
		
		# If post is simple repost, ensure poster has just one simple repost
		if self.is_simple_repost:
			if ArtistPost.objects.filter(
				parent=self.parent,
				poster=self.poster
			).exists():
				raise ValidationError(
					_('User already has simple repost on this post'),
					code='invalid'
				)

	def save(self, *args, **kwargs):
		self.clean()
		super().save(*args, **kwargs)

	class Meta:
		# See https://stackoverflow.com/a/1628855/ for why this syntax is used.
		db_table = 'posts\".\"artist_post'
		ordering = ['-created_on']
		indexes = [
			models.Index(
				fields=['-created_on'], 
				# Index names cannot be longer than 30 characters.
				name='artist_post_desc_idx'
			),
			models.Index(
				fields=['is_simple_repost'],
				name='artist_post_repost_idx'
			)
		]
		# constraints = [
		# 	# Use trigger instead since this references a related field
		# 	models.CheckConstraint(
		# 		check=Q(pinned_comment__is_parent=True),
		# 		name='pinned_artist_post_comment_is_parent'
		# 	)
		# ]


class ArtistPostRepost(ArtistPost):
	"""Proxy model to operate on artist posts reposts"""
	objects = ArtistPostRepostManager()

	class Meta:
		proxy = True


class ArtistParentPost(ArtistPost):
	"""Proxy model to operate on parent artist posts"""
	objects = ArtistParentPostManager()

	class Meta:
		proxy = True


class ArtistPostPhoto(models.Model, PostMediaMixin):
	post = models.ForeignKey(
		ArtistPost,
		verbose_name=_('Post'),
		db_column='artist_post_id',
		on_delete=models.CASCADE,
		related_name='photos',
		related_query_name='photo'
	)

	# Use width_field and height_field to optimize getting photo's width and height
	photo = ThumbnailerImageField(
		thumbnail_storage=FILE_STORAGE_CLASS(), 
		upload_to=artist_post_photo_upload_path,
		resize_source=dict(size=(250, 250), sharpen=True),
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
		db_table = 'posts\".\"artist_post_photo'

	
class ArtistPostVideo(models.Model, PostMediaMixin):
	post = models.OneToOneField(
		ArtistPost,
		verbose_name=_('Post'),
		db_column='artist_post_id',
		on_delete=models.CASCADE,
		related_name='video',
		related_query_name='video'
	)
	video = DynamicStorageFileField(
		# Depending on whether this video was first an audio, we'll know the directory to upload to.
		# But by default, upload all videos to this directory.
		upload_to=artist_post_video_upload_path, 
		validators=[
			FileExtensionValidator(['mp4', 'mov']), 
			validate_post_video_file
		]
	)
	# Since users can post audio that will ultimately be converted to video,
	# this attribute is to determine whether or not the uploaded file was an audio.
	was_audio = models.BooleanField(editable=False, default=False)

	def __str__(self):
		return f'Post {str(self.post)} video'

	class Meta:
		db_table = 'posts\".\"artist_post_video'


class HashtaggedArtistPost(TaggedItemBase):
	"""Hashtag and ArtistPost through model"""

	# DON'T rename this field !!
	# django-taggit says the name `content_object` must be used
	content_object = models.ForeignKey(
		ArtistPost,
		on_delete=models.CASCADE,
		db_column='artist_post_id',
		related_name='hashtagged_hashtags',
		related_query_name='hashtagged_hashtag'
	)
	# django-taggit says the name `tag` must be used
	tag = models.ForeignKey(
		PostHashtag,
		on_delete=models.CASCADE,
		db_column='post_hashtag_id',
		related_name='hashtagged_artist_posts',
		# When related_query_name is used, it errors are raised when trying to
		# get tags via `post.hashtags.all()`; perhaps they don't support scenarios where
		# the related_name is different from the related_query_name.
		# Furthermore, in django-taggit's documentation, there's no area where
		# they use related_query_name. So let's just stick with only related_name like them.
	)

	class Meta:
		db_table = 'posts\".\"artist_post_with_hashtag'


class ArtistPostMention(models.Model):
	"""Artist post and user mention through model"""

	post = models.ForeignKey(
		ArtistPost,
		db_column='artist_post_id',
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
		db_table = 'posts\".\"artist_post_user_mention'
		constraints = [
			models.UniqueConstraint(
				fields=['post', 'user_mentioned'],
				name='unique_artist_post_user_mention'
			),
		]


class ArtistPostRating(PostRating):
	"""Artist post and rater through model"""

	post = models.ForeignKey(
		ArtistPost,
		db_column='artist_post_id',
		on_delete=models.CASCADE,
		related_name='ratings',
		related_query_name='rating',
	)
	rater = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		db_column='user_id',
		on_delete=models.CASCADE,
		related_name='artist_post_ratings',
		related_query_name='artist_post_rating',
	)

	def __str__(self):
		return f'Post {str(self.post)} rated {self.num_stars} star(s) by {str(self.rater)}'
	
	class Meta:
		db_table = 'posts\".\"artist_post_rating'
		constraints = [
			models.UniqueConstraint(
				fields=['post', 'rater'],
				name='unique_artist_post_rating'
			),
			models.CheckConstraint(
				check=Q(num_stars=1) | Q(num_stars=3) | Q(num_stars=5),
				name='artist_post_rating_stars_is_1_or_3_or_5'
			)
		]


class ArtistPostBookmark(models.Model):
	"""Artist post and bookmarker through model"""

	post = models.ForeignKey(
		ArtistPost,
		db_column='artist_post_id',
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
		db_table = 'posts\".\"artist_post_bookmark'
		constraints = [
			models.UniqueConstraint(
				fields=['post', 'bookmarker'],
				name='unique_artist_post_bookmark'
			),
		]


class ArtistPostDownload(models.Model):
	"""Artist post and downloader through model"""

	post = models.ForeignKey(
		ArtistPost,
		db_column='artist_post_id',
		on_delete=models.CASCADE,
		related_name='+'
	)
	downloader = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		db_column='user_id',
		on_delete=models.CASCADE,
		# These will permit querying on the through model,
		# such as querying on the downloaded_on field.
		# see https://gist.github.com/jacobian/827937 -- 
		# (see test_member_groups() method)
		related_name='artist_post_downloads',
		related_query_name='artist_post_download'
	)
	downloaded_on = models.DateTimeField(auto_now_add=True, editable=False)

	def __str__(self):
		return f'Post {str(self.post)} downloaded by {str(self.downloader)}'
	
	class Meta:
		db_table = 'posts\".\"artist_post_download'


class ArtistPostComment(Comment, FlagMixin, UsesCustomSignal):
	# A parent comment is a comment 
	parent = models.ForeignKey(
		'self',
		on_delete=models.SET_NULL,
		related_name='replies',
		related_query_name='reply',
		db_column='parent_comment_id',
		# Is nullable since comment can be direct comment on post 
		# hence it doesn't have a parent comment or its parent may be deleted.
		# For instance, if a YouTube sub comment is deleted, replies aren't deleted.
		#
		# In other words, only ancestor comments will have this attribute set to null.
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
		# hence it doesn't have an ancestor comment. 
		# Ancestor comments will have this attribute set to null
		blank=True,
		null=True
	)
	poster = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		db_column='user_id',
		on_delete=models.CASCADE,
		related_name='overall_artist_post_comments',
		related_query_name='artist_post_comment'
	)
	likers = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		through='ArtistPostCommentLike',
		related_name='liked_artist_post_comments',
		related_query_name='liked_artist_post_comment'
	)
	users_mentioned = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		through='ArtistPostCommentMention',
		related_name='mentioned_in_artist_post_comment',
		related_query_name='mentioned_in_artist_post_comment',
		blank=True
	)
	# Post on which comment was made
	post_concerned = models.ForeignKey(
		ArtistPost,
		db_column='artist_post_concerned_id',
		on_delete=models.CASCADE,
		related_name='overall_comments',
		related_query_name='comment'
	)

	class Meta: 
		db_table = 'posts\".\"artist_post_comment'
		ordering = ['-num_likes', '-created_on', '-num_child_comments']


class ArtistPostCommentLike(CommentLike):
	comment = models.ForeignKey(
		ArtistPostComment,
		db_column='artist_post_comment_id',
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
		db_table = 'posts\".\"artist_post_comment_like'
		constraints = [
			models.UniqueConstraint(
				fields=['comment', 'liker'],
				name='unique_artist_post_comment_like'
			),
		]


class ArtistPostCommentMention(models.Model):
	"""Artist post comment and user mention through model"""

	comment = models.ForeignKey(
		ArtistPostComment,
		db_column='artist_post_comment_id',
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
		db_table = 'posts\".\"artist_post_comment_user_mention'
		constraints = [
			models.UniqueConstraint(
				fields=['comment', 'user_mentioned'],
				name='unique_artist_post_comment_user_mention'
			),
		]

