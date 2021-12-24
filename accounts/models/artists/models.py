from django.db import models
from django.utils.text import slugify
from django_countries.fields import CountryField
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager
from taggit.models import TagBase, TaggedItemBase

from core.constants import GENDERS
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
	date_of_birth = models.DateField(_('Date of birth'))
	tags = TaggableManager(
		verbose_name=_('Tags'), 
		through='TaggedArtist',
		related_name='artists',
		blank=True
	)
	num_posts = models.PositiveIntegerField(default=0, editable=False)
	added_on = models.DateTimeField(
		_('Added on'),
		auto_now_add=True, 
		editable=False
	)

	class Meta:
		db_table = 'accounts\".\"artist'
		ordering = ['name']

	def __str__(self):
		return f'{self.name}'

	def save(self, *args, **kwargs):
		if not self.pk:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)

		# Add artist's nationality to tags
		self.tags.add(self.country)


class ArtistPhoto(models.Model):
	artist = models.ForeignKey(
		Artist,
		verbose_name=_('Artist'),
		db_column='artist_id',
		on_delete=models.CASCADE,
		related_name='photos',
		related_query_name='photo'
	)

	# Use width_field and height_field to optimize getting photo's width and height
	photo = models.ImageField(width_field='photo_width', height_field='photo_height')
	photo_width = models.PositiveIntegerField(_('Photo width'))
	photo_height = models.PositiveIntegerField(_('Photo height'))
	added_on = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-added_on']
		db_table = 'accounts\".\"artist_photo'


# See django-taggit docs on how to use a Custom tag
# djanto-taggit.readthedocs.io/en/latest/custom_tagging.html
class ArtistTag(TagBase, ArtistTagOperations):
	# Overrode name and slug coz name's maxlength is 100 and slug is 100.
	# this is bad coz if name is say 100(though almost impossible), slug will be >100 chars.
	name = models.CharField(_('Name'), unique=True, max_length=30)
	slug = models.SlugField(unique=True, max_length=50, editable=False)

	class Meta:
		db_table = 'accounts\".\"artist_tag'


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

