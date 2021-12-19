from django.conf.global_settings import LANGUAGES
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from shortuuid.django_fields import ShortUUIDField
from taggit.managers import TaggableManager
from taggit.models import TagBase, TaggedItemBase

from accounts.models import Artist

User = get_user_model()


class Post(models.Model):
	# This will be displayed in the url and will be used rather
	# than the numeric auto-incrementing id.
	# 
	# Since unique=True, django will automatically create an index for this field.
	uuid = ShortUUIDField(
		length=16,
		unique=True,
		max_length=24,
	)
	# The language will be detected via an external language-recognition tool
	language = models.CharField(
		choices=LANGUAGES,
		default='en',
		max_length=7
	)
	created_on = models.DateTimeField(auto_now_add=True, editable=False)
	num_stars = models.PositiveIntegerField(default=0, editable=False)
	num_bookmarks = models.PositiveIntegerField(default=0, editable=False)
	num_views = models.PositiveIntegerField(default=0, editable=False)
	num_downloads = models.PositiveIntegerField(default=0, editable=False)
	num_reposts = models.PositiveIntegerField(default=0, editable=False)

	class Meta:
		abstract = True


class ArtistPost(Post):
	hashtags = TaggableManager(
		verbose_name=_('Hashtags'), 
		through='HashtaggedArtistPost'
	)
	owner = models.ForeignKey(
		User,
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
		related_query_name='artist_post',
		db_column='artist_id'
	)
	music_title = models.CharField(
		_('Music title'), 
		max_length=50
	)
	raters = models.ManyToManyField(
		User,
		through='ArtistPostRating',
		related_name='rated_artist_posts',
		related_query_name='artist_post',
		blank=True
	)
	reposters = models.ManyToManyField(
		User,
		through='ArtistPostRepost',
		related_name='reposted_artist_posts',
		related_query_name='artist_post',
		blank=True
	)
	bookmarkers = models.ManyToManyField(
		User,
		through='ArtistPostBookmark',
		related_name='bookmarked_artist_posts',
		related_query_name='artist_post',
		blank=True
	)
	downloaders = models.ManyToManyField(
		User,
		through='ArtistPostDownload',
		related_name='downloaded_artist_posts',
		related_query_name='artist_post',
		blank=True
	)

	class Meta:
		db_table = 'artist_post'
		ordering = ['-created_on']
		indexes = [
			models.Index(
				fields=['-created_on'], 
				name='artist_post_created_on_desc_idx'
			)
		]


class NonArtistPost(Post):
	hashtags = TaggableManager(
		verbose_name=_('Hashtags'), 
		through='HashtaggedNonArtistPost'
	)
	owner = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		related_name='non_artist_posts',
		related_query_name='non_artist_post',
		db_column='user_id'
	)
	raters = models.ManyToManyField(
		User,
		through='NonArtistPostRating',
		related_name='rated_non_artist_posts',
		related_query_name='non_artist_post',
		blank=True
	)
	reposters = models.ManyToManyField(
		User,
		through='NonArtistPostRepost',
		related_name='reposted_non_artist_posts',
		related_query_name='non_artist_post',
		blank=True
	)
	bookmarkers = models.ManyToManyField(
		User,
		through='NonArtistPostBookmark',
		related_name='bookmarked_non_artist_posts',
		related_query_name='non_artist_post',
		blank=True
	)
	downloaders = models.ManyToManyField(
		User,
		through='NonArtistPostDownload',
		related_name='downloaded_non_artist_posts',
		related_query_name='non_artist_post',
		blank=True
	)

	class Meta:
		db_table = 'non_artist_post'
		ordering = ['-created_on']
		indexes = [
			models.Index(
				fields=['-created_on'], 
				name='non_artist_post_created_on_desc_idx'
			)
		]


# See django-taggit docs on how to use a Custom tag
# djanto-taggit.readthedocs.io/en/latest/custom_tagging.html
class PostHashtag(TagBase):
	# Remember hashtags do not have to contain spaces
	# thus it is sensible to set the name and slug to the same length.
	# As a matter of fact, the name and the slug will always be the same.
	name = models.CharField(
		verbose_name=pgettext_lazy('Hashtag name', 'name'),
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
		db_table = 'post_hashtag'


class HashtaggedArtistPost(TaggedItemBase):
	# DON'T rename this field !!
	# django-taggit says the name `content_object` must be used
	content_object = models.ForeignKey(
		ArtistPost,
		on_delete=models.CASCADE,
		db_column='artist_post_id'
	)
	# django-taggit says the name `tag` must be used
	tag = models.ForeignKey(
		PostHashtag,
		on_delete=models.CASCADE,
		related_name='artist_posts',
		related_query_name='artist_post',
		db_column='post_hashtag_id'
	)

	class Meta:
		db_table = 'artist_post_with_hashtag'


class HashtaggedNonArtistPost(TaggedItemBase):
	# DON'T rename this field !!
	# django-taggit says the name `content_object` must be used
	content_object = models.ForeignKey(
		NonArtistPost,
		on_delete=models.CASCADE,
		db_column='non_artist_post_id'
	)
	# django-taggit says the name `tag` must be used
	tag = models.ForeignKey(
		PostHashtag,
		on_delete=models.CASCADE,
		related_name='non_artist_posts',
		related_query_name='non_artist_post',
		db_column='post_hashtag_id'
	)

	class Meta:
		db_table = 'non_artist_post_with_hashtag'


class PostRating(models.Model):
	num_stars = models.PositiveIntegerField(default=0, editable=False)
	rated_on = models.DateTimeField(auto_now_add=True, editable=False)

	class Meta:
		abstract = True


class ArtistPostRating(PostRating):
	"""
	Artist and PostRating through table
	"""
	rater = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE,
		related_name='artist_post_ratings',
		related_query_name='artist_post_rating',
	)
	post = models.ForeignKey(
		ArtistPost,
		db_column='artist_post_id',
		on_delete=models.CASCADE,
		related_name='ratings',
		related_query_name='rating',
	)

	class Meta:
		db_table = 'artist_post_rating'
		constraints = [
			models.UniqueConstraint(
				fields=['rater', 'post'],
				name='unique_artist_post_rating'
			),
		]


class NonArtistPostRating(PostRating):
	rater = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE,
		related_name='non_artist_post_ratings',
		related_query_name='non_artist_post_rating',
	)
	post = models.ForeignKey(
		NonArtistPost,
		db_column='non_artist_post_id',
		on_delete=models.CASCADE,
		related_name='ratings',
		related_query_name='rating',
	)

	class Meta:
		db_table = 'non_artist_post_rating'
		constraints = [
			models.UniqueConstraint(
				fields=['rater', 'post'],
				name='unique_non_artist_post_rating'
			),
		]


class ArtistPostRepost(models.Model):
	reposter = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE,
		related_name='artist_post_reposts',
		related_query_name='artist_post_repost',
	)
	post = models.ForeignKey(
		ArtistPost,
		db_column='artist_post_id',
		on_delete=models.CASCADE,
		related_name='reposts',
		related_query_name='repost',
	)
	reposted_on = models.DateTimeField(auto_now_add=True, editable=False)

	class Meta:
		db_table = 'artist_post_repost'
		ordering = ['-reposted_on']
		constraints = [
			models.UniqueConstraint(
				fields=['reposter', 'post'],
				name='unique_artist_post_repost'
			),
		]


class NonArtistPostRepost(models.Model):
	reposter = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE,
		related_name='non_artist_post_reposts',
		related_query_name='non_artist_post_repost',
	)
	post = models.ForeignKey(
		NonArtistPost,
		db_column='non_artist_post_id',
		on_delete=models.CASCADE,
		related_name='reposts',
		related_query_name='repost',
	)
	reposted_on = models.DateTimeField(auto_now_add=True, editable=False)

	class Meta:
		db_table = 'non_artist_post_repost'
		ordering = ['-reposted_on']
		constraints = [
			models.UniqueConstraint(
				fields=['reposter', 'post'],
				name='unique_non_artist_post_repost'
			),
		]


class ArtistPostBookmark(models.Model):
	bookmarker = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE
	)
	post = models.ForeignKey(
		ArtistPost,
		db_column='artist_post_id',
		on_delete=models.CASCADE
	)
	bookmarked_on = models.DateTimeField(auto_now_add=True, editable=False)

	class Meta:
		db_table = 'artist_post_bookmark'
		constraints = [
			models.UniqueConstraint(
				fields=['bookmarker', 'post'],
				name='unique_artist_post_bookmark'
			),
		]


class NonArtistPostBookmark(models.Model):
	bookmarker = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE
	)
	post = models.ForeignKey(
		NonArtistPost,
		db_column='non_artist_post_id',
		on_delete=models.CASCADE
	)
	bookmarked_on = models.DateTimeField(auto_now_add=True, editable=False)

	class Meta:
		db_table = 'non_artist_post_bookmark'
		constraints = [
			models.UniqueConstraint(
				fields=['bookmarker', 'post'],
				name='unique_non_artist_post_bookmark'
			),
		]


class ArtistPostDownload(models.Model):
	downloader = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE
	)
	post = models.ForeignKey(
		ArtistPost,
		db_column='artist_post_id',
		on_delete=models.CASCADE
	)
	downloaded_on = models.DateTimeField(auto_now_add=True, editable=False)

	class Meta:
		db_table = 'artist_post_download'


class NonArtistPostDownload(models.Model):
	downloader = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE
	)
	post = models.ForeignKey(
		NonArtistPost,
		db_column='non_artist_post_id',
		on_delete=models.CASCADE
	)
	downloaded_on = models.DateTimeField(auto_now_add=True, editable=False)

	class Meta:
		db_table = 'non_artist_post_download'

	
class ArtistPostImage(models.Model):
	post = models.ForeignKey(
		ArtistPost,
		db_column='artist_post_id',
		on_delete=models.CASCADE
	)

	# Use width_field and height_field to optimize getting image's width and height
	image = models.ImageField(width_field='image_width', height_field='image_height')

	image_width = models.PositiveIntegerField()
	image_height = models.PositiveIntegerField()
	type = models.CharField(choices=())

	class Meta:
		db_table = 'artist_post_image'


class NonArtistPostImage(models.Model):
	post = models.ForeignKey(
		NonArtistPost,
		db_column='non_artist_post_id',
		on_delete=models.CASCADE
	)
	image = models.ImageField(width_field='image_width', height_field='image_height')
	image_width = models.PositiveIntegerField()
	image_height = models.PositiveIntegerField()
	type = models.CharField(choices=())

	class Meta:
		db_table = 'non_artist_post_image'
		
	
class ArtistPostVideo(models.Model):
	post = models.ForeignKey(
		ArtistPost,
		db_column='artist_post_id',
		on_delete=models.CASCADE
	)
	video = models.FileField()

	class Meta:
		db_table = 'artist_post_video'


class NonArtistPostVideo(models.Model):
	post = models.ForeignKey(
		NonArtistPost,
		db_column='non_artist_post_id',
		on_delete=models.CASCADE
	)
	video = models.FileField()

	class Meta:
		db_table = 'non_artist_post_video'


class Comment(models.Model):
	body = models.TextField(

	)
	created_on = models.DateTimeField(auto_now_add=True, editable=False)
	num_likes = models.PositiveIntegerField(default=0, editable=False)
	
	class Meta:
		abstract = True


class ArtistPostComment(Comment):
	owner = models.ForeignKey(
		User,
		db_column='user_id'
	)
	post = models.ForeignKey(
		ArtistPost,
		db_column='artist_post_id'
	)
	likers = models.ManyToManyField(
		User,
		through='ArtistPostCommentLike',
		related_name='liked_artist_post_comments',
		related_query_name='artist_post_comment'
	)

	class Meta: 
		db_table = 'artist_post_comment'


class NonArtistPostComment(Comment):
	owner = models.ForeignKey(
		User,
		db_column='user_id'
	)
	post = models.ForeignKey(
		NonArtistPost,
		db_column='non_artist_post_id'
	)
	likers = models.ManyToManyField(
		User,
		through='NonArtistPostCommentLike',
		related_name='liked_non_artist_post_comments',
		related_query_name='non_artist_post_comment'
	)

	class Meta: 
		db_table = 'non_artist_post_comment'


class CommentLike(models.Model):
	liked_on = models.DateTimeField(auto_now_add=True, editable=False)

	class Meta:
		abstract = True


class ArtistPostCommentLike(CommentLike):
	liker = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE
	)
	comment = models.ForeignKey(
		ArtistPostComment,
		db_column='artist_post_comment_id',
		on_delete=models.CASCADE
	)

	class Meta:
		db_table = 'artist_post_comment_like'
		constraints = [
			models.UniqueConstraint(
				fields=['liker', 'post'],
				name='unique_artist_post_comment_like'
			),
		]


class NonArtistPostCommentLike(CommentLike):
	liker = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE
	)
	comment = models.ForeignKey(
		NonArtistPostComment,
		db_column='non_artist_post_comment_id',
		on_delete=models.CASCADE
	)

	class Meta:
		db_table = 'non_artist_post_comment_like'
		constraints = [
			models.UniqueConstraint(
				fields=['liker', 'comment'],
				name='unique_non_artist_post_comment_like'
			),
		]





