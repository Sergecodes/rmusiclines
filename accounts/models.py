from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager
from taggit.models import TagBase, TaggedItemBase

from core.constants import GENDERS


class Artist(models.Model):
	# Remember only staff is permitted to add an artist
	username = models.CharField(
		_('Username'),
		unique=True,
		
	)
	display_name = models.CharField(

	)
	nationality = models.CharField(

	)
	tags = TaggableManager(
		verbose_name=_('Tags'), 
		through='TaggedArtist'
	)

	class Meta:
		db_table = 'artist'


# See django-taggit docs on how to use a Custom tag
# djanto-taggit.readthedocs.io/en/latest/custom_tagging.html
class ArtistTag(TagBase):
	# Overrode name and slug coz name's maxlength is 100 and slug is 100.
	# this is bad coz if name is say 100(though almost impossible), slug will be >100 chars.
	name = models.CharField(_('Name'), unique=True, max_length=30)
	slug = models.SlugField(unique=True, max_length=100)

	class Meta:
		verbose_name = _('Artist Tag')
		verbose_name_plural = _('Artist Tags')
		db_table = 'artist_tag'


class TaggedArtist(TaggedItemBase):
	# DON'T rename this field !!
	# django-taggit says the name `content_object` must be used
	content_object = models.ForeignKey(
		Artist,
		on_delete=models.CASCADE,
		db_column='artist_id'
	)
	# django-taggit says the name `tag` must be used
	tag = models.ForeignKey(
		ArtistTag,
		on_delete=models.CASCADE,
		related_name='artists',
		related_query_name='artist',
		db_column='artist_tag_id'
	)

	class Meta:
		db_table = 'artist_with_tag'


class User(AbstractBaseUser, PermissionsMixin):
	# username = models.CharField(
	# 	_('Username'),
	# 	max_length=15,
	# 	unique=True,
	# 	help_text=_(
	# 		'Your username should be between 4 to 15 characters '
	# 		'and the first 4 characters must be letters. <br> '
	# 		'It should not contain any symbols, dashes or spaces. <br>'
	# 		'All other characters are allowed (letters, numbers, hyphens and underscores).'
	# 	),
	# 	error_messages={
	# 		'unique': _('A user with that username already exists.'),
	# 	},
	# 	validators=[UsernameValidator()]
	# )
	display_name = models.CharField(

	)
	country = models.CharField(

	)
	bio = models.TextField()
	date_of_birth = models.DateField()
	profile_image = models.ImageField(
		width_field='profile_image_width', 
		height_field='profile_image_height'
	)
	profile_image_width = models.PositiveIntegerField()
	profile_image_height = models.PositiveIntegerField()
	cover_photo = models.ImageField(
		width_field='cover_photo_width',
		height_field='cover_photo_height'
	)
	cover_photo_width = models.PositiveIntegerField()
	cover_photo_height = models.PositiveIntegerField()

	gender = models.CharField(
		_('Gender'),
		choices=GENDERS,
		default='M',
		max_length=2,
	)
	date_joined = models.DateTimeField(_('Date joined'), auto_now_add=True, editable=False)
	is_superuser = models.BooleanField(default=False)
	# Staff in company(website)
	is_staff = models.BooleanField(default=False)   
	# Site moderator
	is_mod = models.BooleanField(default=False)   # site moderator
	# Can user login ? set to False by default since user has to confirm email address...
	is_active = models.BooleanField(default=False)  
	is_verified = models.BooleanField(default=False)
	is_premium = models.BooleanField(default=False)
	verified_on = models.DateTimeField(null=True, blank=True, editable=False)
	deactivated_on = models.DateTimeField(
		null=True, blank=True, 
		editable=False
	)

	# Other users related info
	blocked_users = models.ManyToManyField(
		'self',
		through='UserBlocking',
		related_name='blocked_by',
		related_query_name='blocked_user',
		symmetrical=False
	)
	followers = models.ManyToManyField(
		'self',
		through='UserFollow',
		related_name='following',
		related_query_name='following_user',
		symmetrical=False,
	)

	# Post related info
	num_followers = models.PositiveIntegerField(default=0)
	num_following = models.PositiveIntegerField(default=0)
	num_artist_related_posts = models.PositiveIntegerField(default=0)
	num_non_artist_related_posts = models.PositiveIntegerField(default=0)
	num_artist_related_post_comments = models.PositiveIntegerField(default=0)
	num_non_artist_related_post_comments = models.PositiveIntegerField(default=0)

	USERNAME_FIELD = 'email'
	# USERNAME_FIELD and password are required by default
	REQUIRED_FIELDS = ['username', 'display_name']   

	# objects = UserManager()
	# active = ActiveUserManager()
	# moderators = ModeratorManager()
	# staff = StaffManager()
	# premium = PremiumUserManager()
	# verified = VerifiedUserManager()

	class Meta:
		db_table = 'user'
	
	def __str__(self):
		return f'{self.display_name}, @{self.username}'

	@property
	def is_suspended(self):
		pass

	def deactivate(self):
		"""Mark user as inactive but allow his record in database."""
		# Don't actually delete user account, just do this instead
		self.deactivated_on = timezone.now()
		self.is_active = False
		self.save(update_fields=['is_active', 'deactivated_on'])

	def delete(self, *args, **kwargs):
		really_delete = kwargs.pop('really_delete', False)

		if really_delete:
			return super().delete(*args, **kwargs) 
		else:
			self.deactivate()
			# print("User's account deactivated successfully")
	
	def get_absolute_url(self):
		pass


class UserBlocking(models.Model):
	blocker = models.ForeignKey(
		User,
		db_column='user_id'
	)
	blocked = models.ForeignKey(
		User,
		db_column='user_id'
	)

	class Meta:
		db_table = 'user_blocking'
		constraints = [
			models.UniqueConstraint(
				fields=['blocker', 'blocked'],
				name='unique_user_blocking'
			),
		]


class UserFollow(models.Model):
	follower = models.ForeignKey(
		User,
		db_column='user_id'
	)
	following = models.ForeignKey(
		User,
		db_column='user_id'
	)

	class Meta:
		db_table = 'user_follow'
		constraints = [
			models.UniqueConstraint(
				fields=['follower', 'following'],
				name='unique_user_follow'
			),
		]


class Suspension(models.Model):
	SUSPENSION_PERIODS = (

	)

	user = models.ForeignKey(
		User, 
		db_column='user_id', 
		on_delete=models.CASCADE
	)
	suspended_on = models.DateTimeField(auto_now_add=True)
	period = models.DurationField(choices=SUSPENSION_PERIODS)
	over_on = models.DateTimeField()

	def save(self, *args, **kwargs):
		if not self.id:
			self.over_on = self.suspended_on + self.period

		super().save(*args, **kwargs)

	@property
	def is_active(self):
		return self.over_on > timezone.now()

	class Meta:
		db_table = 'suspension'


class Setting(models.Model):
	user = models.OneToOneField(User, db_column='user_id')
	notification_setting = models.JSONField(default=dict)
	site_setting = models.JSONField(defaut=dict)

	class Meta:
		db_table = 'setting'


