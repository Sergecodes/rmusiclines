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

from accounts.constants import (
	ARTIST_MAX_AGE, ARTIST_MIN_AGE,
	ARTISTS_PHOTOS_UPLOAD_DIR
)
from accounts.utils import get_age
from core.constants import GENDERS, FILE_STORAGE_CLASS
from .operations import ArtistOperations, ArtistTagOperations


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
		related_name='artists',
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

	def clean(self):
		# Validate artist's age
		age = get_age(self.birth_date)

		if not (age >= ARTIST_MIN_AGE and age <= ARTIST_MAX_AGE):
			raise ValidationError(
				_('Artists must be at least %d and at most %d years old.' % (
					ARTIST_MIN_AGE, ARTIST_MAX_AGE
				))
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
		upload_to=ARTISTS_PHOTOS_UPLOAD_DIR,
		resize_source=dict(size=(1800, 1800), sharpen=True),
		validators=[FileExtensionValidator(['png, jpg, gif'])],
		width_field='photo_width', 
		height_field='photo_height'
	)
	photo_width = models.PositiveIntegerField()
	photo_height = models.PositiveIntegerField()
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

	# def clean(self):
	# 	# Tags should be alphabetic and con contain spaces
	# 	# but no leading nor trailing spaces
	# 	tag = self.name

	# 	if tag.startswith(' ') or tag.endswith(' '):
	# 		raise ValidationError(
	# 			_(
	# 				"Tags should be alphabetic(can not contain symbols nor leading "
	# 				"or trailing space)"
	# 			)
	# 		)

	# 	# Remove space from tag so as to verify
	# 	# if tag has only alphabetic characters
	# 	tag = tag.replace(' ', '')
	# 	if not tag.isalpha():
	# 		raise ValidationError(
	# 			_(
	# 				"Tags should be alphabetic(can not contain symbols nor leading "
	# 				"or trailing space)"
	# 			)
	# 		)
		
	# def save(self, *args, **kwargs):
	# 	self.clean()

	# 	# No need to slugify tag name to get slug, 
	# 	# django-taggit's TagBase model which is inherited does this by default.
	# 	super().save(*args, **kwargs)

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
		related_name='+'
	)
	# django-taggit says the name `tag` must be used
	tag = models.ForeignKey(
		ArtistTag,
		on_delete=models.CASCADE,
		db_column='artist_tag_id',
		related_name='+'
	)

	class Meta:
		db_table = 'accounts\".\"artist_with_tag'

