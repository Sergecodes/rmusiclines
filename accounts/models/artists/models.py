from django_countries.fields import CountryField
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.fields import ThumbnailerImageField
from taggit.managers import TaggableManager
from taggit.models import TagBase, TaggedItemBase

from accounts.constants import ARTIST_MAX_AGE, ARTIST_MIN_AGE, ARTISTS_PHOTOS_UPLOAD_DIR
from accounts.utils import get_age, get_artist_photos_upload_path as get_upload_path
from core.constants import GENDERS, FILE_STORAGE_CLASS
from .operations import ArtistOperations, ArtistTagOperations


def get_artist_photo_upload_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/artists/artist_<slug>/artist_photos/<filename>
	return get_upload_path(instance.artist.slug, ARTISTS_PHOTOS_UPLOAD_DIR, filename)


class Artist(models.Model, ArtistOperations):
	# Remember only staff is permitted to add an artist
	name = models.CharField(
		_('Name'),
		unique=True,
		max_length=50
	)
	slug = models.SlugField(
		unique=True,
		max_length=80,
		editable=False
	)
	country = CountryField(
		verbose_name=_('Country of origin'),
		blank_label=_('(select country)'),
	)
	gender = models.CharField(
		_('Gender'),
		choices=GENDERS,
		default='M',
		max_length=3
	)
	birth_date = models.DateField(_('Date of birth'))
	tags = TaggableManager(
		verbose_name=_('Tags'), 
		through='TaggedArtist',
		blank=True
	)
	followers = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		through='ArtistFollow',
		related_name='following_artists',
		related_query_name='following_artist'
	)
	num_followers = models.PositiveIntegerField(default=0, editable=False)
	num_posts = models.PositiveIntegerField(default=0, editable=False)
	added_on = models.DateTimeField(
		_('Added on'),
		auto_now_add=True, 
		editable=False
	)

	def __str__(self):
		return self.name

	@property
	def get_tags(self):
		"""Return list of tags. Used in the graphql api to get tags of an artist."""
		return list(self.tags.all())

	def clean(self):
		# Validate artist's age
		age = get_age(self.birth_date)

		if not (age >= ARTIST_MIN_AGE and age <= ARTIST_MAX_AGE):
			raise ValidationError(
				_('Artists must be at least %d and at most %d years old.' % (
						ARTIST_MIN_AGE, ARTIST_MAX_AGE
					)
				),
				code='invalid'
			)
			
	def save(self, *args, **kwargs):
		if not self.pk:
			self.slug = slugify(self.name)

		self.clean()
		super().save(*args, **kwargs)

		# Add artist's nationality to tags
		self.tags.add(self.country.name)

	class Meta:
		db_table = 'accounts\".\"artist'
		ordering = ['name']
		## Check constraint on table:
		# ALTER TABLE accounts.user ADD CONSTRAINT "age_gte_13_and_lte_120" CHECK (
		# 	birth_date <= (now()::date - '13 years'::interval) AND 
		# 	birth_date >= (now()::date - '120 years'::interval)
		# )
		#
		# It can't be set here coz we need the current time and timezone.now() 
		# can't work since it will give the time when the constraint is created
		# not the time when artist's account is getting created.


class ArtistFollow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column='user_id',
        on_delete=models.CASCADE,
        related_name='+'
    )
    artist = models.ForeignKey(
        Artist,
        db_column='artist_id',
        on_delete=models.CASCADE,
        related_name='+'
    )
    followed_on = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return f'{str(self.follower)} follows {str(self.artist)}'

    class Meta:
        db_table = 'accounts\".\"artist_follow'
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'artist'],
                name='unique_user_artist_follow'
            ),
        ]


class ArtistPhoto(models.Model):
	artist = models.ForeignKey(
		Artist,
		db_column='artist_id',
		on_delete=models.CASCADE,
		related_name='photos',
		related_query_name='photo'
	)

	# Use width_field and height_field to optimize getting photo's width and height
	photo = ThumbnailerImageField(
		thumbnail_storage=FILE_STORAGE_CLASS(), 
		upload_to=get_artist_photo_upload_path,
		resize_source=dict(size=(600, 600), sharpen=True),
		validators=[FileExtensionValidator(['png, jpg'])],
		width_field='photo_width', 
		height_field='photo_height'
	)
	photo_width = models.PositiveIntegerField()
	photo_height = models.PositiveIntegerField()
	uploaded_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		db_column='user_id',
		# If uploader is deleted, keep photos but mark uploader as Null
		on_delete=models.SET_NULL,
		related_name='uploaded_artist_photos',
		related_query_name='artist_photo',
		null=True
	)
	uploaded_on = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f'Artist {str(self.artist)} photo'

	class Meta:
		ordering = ['-uploaded_on']
		db_table = 'accounts\".\"artist_photo'


# See django-taggit docs on how to use a Custom tag
# djanto-taggit.readthedocs.io/en/latest/custom_tagging.html
class ArtistTag(TagBase, ArtistTagOperations):
	# Overrode name and slug coz name's maxlength is 100 and slug is 100.
	# this is bad coz if name is say 100(though almost impossible), slug will be >100 chars.
	name = models.CharField(_('Name'), unique=True, max_length=30)
	slug = models.SlugField(unique=True, max_length=100, editable=False, allow_unicode=True)

	@property
	def artists(self):
		return Artist.objects.filter(tags__in=[self])

	class Meta:
		db_table = 'accounts\".\"artist_tag'
		# constraints = [
		# 	models.CheckConstraint(
		# 		# Tag name should be alphabetic but can contain spaces
		# 		# See https://postgresql.org/docs/current/functions-matching.html
		# 		# (bracket expressions)
		# 		# or ^[[:alpha:]]+(?:\s[[:alpha:]]+)*$
		# 		check=Q(name__regex=r'^[[:alpha:]]+(?:[[:space:]][[:alpha:]]+)*$'),
		# 		name='artist_tag_is_alphabetic'
		# 	)
		# ]


class TaggedArtist(TaggedItemBase):
	"""Through model between Artist and ArtistTag"""
	# DON'T rename this field !!
	# django-taggit says the name `content_object` must be used
	content_object = models.ForeignKey(
		Artist,
		on_delete=models.CASCADE,
		db_column='artist_id',
		related_name='tagged_tags',
		related_query_name='tagged_tag'
	)
	# django-taggit says the name `tag` must be used
	tag = models.ForeignKey(
		ArtistTag,
		on_delete=models.CASCADE,
		db_column='artist_tag_id',
		related_name='tagged_artists',
		# Don't set related_query_name
	)
	# To get all artists of a given tag:
	# Method 1:
	# tag_names = ['tag1', 'tag2']
	# Artist.objects.filter(tags__name__in=[tag_names])
	#
	# Method 2:
	# tagged_artists = tag.tagged_artists.all()
	# artists_list = [tagged_artist.content_object for tagged_artist in tagged_artists]
	#
	# Method 3:
	# Artist.objects.filter(tags=tag)
	
	class Meta:
		db_table = 'accounts\".\"artist_with_tag'

