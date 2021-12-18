from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Artist(models.Model):
	username = models.CharField(
		_('Username'),
		unique=True,
		
	)
	display_name = models.CharField(

	)
	nationality = models.CharField(

	)

	class Meta:
		db_table = 'artist'


class Post(models.Model):
	unique_str = models.CharField(
		unique=True,
	)
	language = models.CharField(
		choices=settings.LANGUAGES
	)
	created_on = models.DateTimeField(
		auto_now_add=True
	)
	num_stars = models.PositiveIntegerField(
		default=0
	)
	num_bookmarks = models.PositiveIntegerField(
		default=0
	)
	num_views = models.PositiveIntegerField(
		default=0
	)
	num_downloads = models.PositiveIntegerField(
		default=0
	)
	num_reposts = models.PositiveIntegerField(
		default=0
	)

	class Meta:
		abstract = True


class ArtistRelatedPost(Post):
	owner = models.ForeignKey(
		User,
		db_column='user_id'
	)
	artist = models.ForeignKey(
		Artist,
		db_column='artist_id'
	)
	music_title = models.CharField(

	)
	raters = models.ManyToManyField(
		User,
		through='ArtistRelatedPostRating',
		related_name='rated_artist_related_posts',
		related_query_name='artist_related_post'
	)
	reposters = models.ManyToManyField(
		User,
		through='ArtistRelatedPostRepost',
		related_name='reposted_artist_related_posts',
		related_query_name='artist_related_post'
	)
	bookmarkers = models.ManyToManyField(
		User,
		through='ArtistRelatedPostBookmark',
		related_name='bookmarked_artist_related_posts',
		related_query_name='artist_related_post'
	)
	downloaders = models.ManyToManyField(
		User,
		through='ArtistRelatedPostDownload',
		related_name='downloaded_artist_related_posts',
		related_query_name='artist_related_post'
	)

	class Meta:
		db_tabe = 'artist_related_post'


class NonArtistRelatedPost(Post):
	owner = models.ForeignKey(
		User,
		db_column='user_id'
	)
	raters = models.ManyToManyField(
		User,
		through='NonArtistRelatedPostRating',
		related_name='rated_non_artist_related_posts',
		related_query_name='non_artist_related_post'
	)
	reposters = models.ManyToManyField(
		User,
		through='NonArtistRelatedPostRepost',
		related_name='reposted_non_artist_related_posts',
		related_query_name='non_artist_related_post'
	)
	bookmarkers = models.ManyToManyField(
		User,
		through='NonArtistRelatedPostBookmark',
		related_name='bookmarked_non_artist_related_posts',
		related_query_name='non_artist_related_post'
	)
	downloaders = models.ManyToManyField(
		User,
		through='NonArtistRelatedPostDownload',
		related_name='downloaded_non_artist_related_posts',
		related_query_name='non_artist_related_post'
	)

	class Meta:
		db_table = 'non_artist_related_post'


# hashtag
# artist_related_post_hashtag
# non_artist_related_post_hashtag
# artist_tag
# artist_artist_tag(artist_with_tag  ?)


class PostRating(models.Model):
	star_count = models.PositiveIntegerField()
	rated_on = models.DateTimeField(auto_now_add=True)

	class Meta:
		abstract = True


class ArtistRelatedPostRating(PostRating):
	rater = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE
	)
	post = models.ForeignKey(
		ArtistRelatedPost,
		db_column='artist_related_post_id',
		on_delete=models.CASCADE
	)

	class Meta:
		db_table = 'artist_related_post_rating'
		constraints = [
			models.UniqueConstraint(
				fields=['rater', 'post'],
				name='unique_artist_post_rating'
			),
		]


class NonArtistRelatedPostRating(PostRating):
	rater = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE
	)
	post = models.ForeignKey(
		NonArtistRelatedPost,
		db_column='non_artist_related_post_id',
		on_delete=models.CASCADE
	)

	class Meta:
		db_table = 'non_artist_related_post_rating'
		constraints = [
			models.UniqueConstraint(
				fields=['rater', 'post'],
				name='unique_non_artist_post_rating'
			),
		]


class ArtistRelatedPostRepost(models.Model):
	reposter = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE
	)
	post = models.ForeignKey(
		ArtistRelatedPost,
		db_column='artist_related_post_id',
		on_delete=models.CASCADE
	)
	reposted_on = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'artist_related_post_repost'
		constraints = [
			models.UniqueConstraint(
				fields=['reposter', 'post'],
				name='unique_artist_post_repost'
			),
		]


class NonArtistRelatedPostRepost(models.Model):
	reposter = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE
	)
	post = models.ForeignKey(
		NonArtistRelatedPost,
		db_column='non_artist_related_post_id',
		on_delete=models.CASCADE
	)
	reposted_on = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'non_artist_related_post_repost'
		constraints = [
			models.UniqueConstraint(
				fields=['reposter', 'post'],
				name='unique_non_artist_post_repost'
			),
		]


class ArtistRelatedPostBookmark(models.Model):
	bookmarker = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE
	)
	post = models.ForeignKey(
		ArtistRelatedPost,
		db_column='artist_related_post_id',
		on_delete=models.CASCADE
	)
	bookmarked_on = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'artist_related_post_bookmark'
		constraints = [
			models.UniqueConstraint(
				fields=['bookmarker', 'post'],
				name='unique_artist_post_bookmark'
			),
		]


class NonArtistRelatedPostBookmark(models.Model):
	bookmarker = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE
	)
	post = models.ForeignKey(
		NonArtistRelatedPost,
		db_column='non_artist_related_post_id',
		on_delete=models.CASCADE
	)
	bookmarked_on = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'non_artist_related_post_bookmark'
		constraints = [
			models.UniqueConstraint(
				fields=['bookmarker', 'post'],
				name='unique_non_artist_post_bookmark'
			),
		]


class ArtistRelatedPostDownload(models.Model):
	downloader = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE
	)
	post = models.ForeignKey(
		ArtistRelatedPost,
		db_column='artist_related_post_id',
		on_delete=models.CASCADE
	)
	downloaded_on = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'artist_related_post_download'


class NonArtistRelatedPostDownload(models.Model):
	downloader = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE
	)
	post = models.ForeignKey(
		NonArtistRelatedPost,
		db_column='non_artist_related_post_id',
		on_delete=models.CASCADE
	)
	downloaded_on = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'non_artist_related_post_download'

	
class ArtistRelatedPostImage(models.Model):
	post = models.ForeignKey(
		ArtistRelatedPost,
		db_column='artist_related_post_id',
		on_delete=models.CASCADE
	)

	# Use width_field and height_field to optimize getting image's width and height
	image = models.ImageField(width_field='image_width', height_field='image_height')

	image_width = models.PositiveIntegerField()
	image_height = models.PositiveIntegerField()
	type = models.CharField(choices=())

	class Meta:
		db_table = 'artist_related_post_image'


class NonArtistRelatedPostImage(models.Model):
	post = models.ForeignKey(
		NonArtistRelatedPost,
		db_column='non_artist_related_post_id',
		on_delete=models.CASCADE
	)
	image = models.ImageField(width_field='image_width', height_field='image_height')
	image_width = models.PositiveIntegerField()
	image_height = models.PositiveIntegerField()
	type = models.CharField(choices=())

	class Meta:
		db_table = 'non_artist_related_post_image'
		
	
class ArtistRelatedPostVideo(models.Model):
	post = models.ForeignKey(
		ArtistRelatedPost,
		db_column='artist_related_post_id',
		on_delete=models.CASCADE
	)
	video = models.FileField()

	class Meta:
		db_table = 'artist_related_post_video'


class NonArtistRelatedPostVideo(models.Model):
	post = models.ForeignKey(
		NonArtistRelatedPost,
		db_column='non_artist_related_post_id',
		on_delete=models.CASCADE
	)
	video = models.FileField()

	class Meta:
		db_table = 'non_artist_related_post_video'


class Comment(models.Model):
	body = models.TextField(

	)
	created_on = models.DateTimeField(
		auto_now_add=True
	)
	num_likes = models.PositiveIntegerField(
		default=0
	)
	
	class Meta:
		abstract = True


class ArtistRelatedPostComment(Comment):
	owner = models.ForeignKey(
		User,
		db_column='user_id'
	)
	post = models.ForeignKey(
		ArtistRelatedPost,
		db_column='artist_related_post_id'
	)
	likers = models.ManyToManyField(
		User,
		through='ArtistRelatedPostCommentLike',
		related_name='liked_artist_related_post_comments',
		related_query_name='artist_related_post_comment'
	)

	class Meta: 
		db_table = 'artist_related_post_comment'


class NonArtistRelatedPostComment(Comment):
	owner = models.ForeignKey(
		User,
		db_column='user_id'
	)
	post = models.ForeignKey(
		NonArtistRelatedPost,
		db_column='non_artist_related_post_id'
	)
	likers = models.ManyToManyField(
		User,
		through='NonArtistRelatedPostCommentLike',
		related_name='liked_non_artist_related_post_comments',
		related_query_name='non_artist_related_post_comment'
	)

	class Meta: 
		db_table = 'non_artist_related_post_comment'


class CommentLike(models.Model):
	liked_on = models.DateTimeField(auto_now_add=True)

	class Meta:
		abstract = True


class ArtistRelatedPostCommentLike(CommentLike):
	liker = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE
	)
	comment = models.ForeignKey(
		ArtistRelatedPostComment,
		db_column='artist_related_post_comment_id',
		on_delete=models.CASCADE
	)

	class Meta:
		db_table = 'artist_related_post_comment_like'
		constraints = [
			models.UniqueConstraint(
				fields=['liker', 'post'],
				name='unique_artist_post_comment_like'
			),
		]


class NonArtistRelatedPostCommentLike(CommentLike):
	liker = models.ForeignKey(
		User,
		db_column='user_id',
		on_delete=models.CASCADE
	)
	comment = models.ForeignKey(
		NonArtistRelatedPostComment,
		db_column='non_artist_related_post_comment_id',
		on_delete=models.CASCADE
	)

	class Meta:
		db_table = 'non_artist_related_post_comment_like'
		constraints = [
			models.UniqueConstraint(
				fields=['liker', 'comment'],
				name='unique_non_artist_post_comment_like'
			),
		]





