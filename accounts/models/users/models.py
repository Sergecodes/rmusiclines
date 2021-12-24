import datetime
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import (
	AbstractBaseUser, 
	UserManager as BaseUserManager,
	PermissionsMixin
)
from django.db import models
from django.db.models import F
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

from core.constants import GENDERS
from .operations import UserOperations
from ...validators import UserUsernameValidator


class UserQuerySet(QuerySet):
	def delete(self, really_delete=False):
		if really_delete:
			return super().delete()
		else:
			self.deactivate()

	def deactivate(self):
		self.update(is_active=False, deactivated_on=timezone.now())


class UserManager(BaseUserManager):
	def _create_user(self, username, email, password, **extra_fields):
		if not username:
			raise ValueError('The given username must be set')

		email = self.normalize_email(email)
		username = User.normalize_username(username)
		
		user = User(username=username, email=email, **extra_fields)
		user.password = make_password(password)
		user.save(using=self._db)

		return user

	def get_queryset(self):
		return UserQuerySet(self.model, using=self._db)


class User(AbstractBaseUser, PermissionsMixin, UserOperations):
	email = models.EmailField(
		_('Email address'),
		max_length=50,
		unique=True,
		help_text=_('We will send a verification code to this email'),
		error_messages={
			'unique': _('A user with that email already exists.'),
			# null, blank, invalid, invalid_choice, unique, unique_for_date
		}
	)
	username = models.CharField(
		_('Username'),
		max_length=15,
		editable=False,
		# Enforce uniqueness via UniqueConstraint
		# unique=True,
		validators=[UserUsernameValidator()],
		help_text=_('Your username should be less than 15 characters.'),
		error_messages={
			'unique': _('A user with that username already exists.'),
		},
		## https://docs.djangoproject.com/en/3.2/ref/contrib/postgres/operations
		# /#managing-colations-using-migrations
		#
		## https://stackoverflow.com/questions/18807276/
		# how-to-make-my-postgresql-database-use-a-case-insensitive-colation
		#
		## https://gist.github.com/hleroy/2f3c6b00f284180da10ed9d20bf9240a
		# how to use Django 3.2 CreateCollation and db_collation to implement a 
		# case-insensitive Chaffield with Postgres > 1
		#
		## https://www.postgresql.org/docs/current/citext.html
		#
		## https://www.postgresql.org/docs/current/collation.html#COLLATION-NONDETERMINISTIC
		db_collation='accounts\".\"case_insensitive'
	)
	display_name = models.CharField(_('Full name'), max_length=50)
	country = CountryField(
		verbose_name=_('Location'),
		blank_label=_('(select country)'),
	)
	date_of_birth = models.DateField(_('Date of birth'))
	bio = models.TextField(_('Bio'))
	profile_photo = models.ImageField(
		_('Profile photo'),
		width_field='profile_photo_width', 
		height_field='profile_photo_height',
		# no null=True needed, since this translates to a char field 
		# and char fields don't need it..
		blank=True  
	)
	cover_photo = models.ImageField(
		_('Cover photo'),
		width_field='cover_photo_width',
		height_field='cover_photo_height',
		# no null=True needed, since this tran
		blank=True  
	)
	# Django specific optimizations for getting width and height of images
	profile_photo_width = models.PositiveIntegerField(default=0)
	profile_photo_height = models.PositiveIntegerField(default=0)
	cover_photo_width = models.PositiveIntegerField(default=0)
	cover_photo_height = models.PositiveIntegerField(default=0)

	gender = models.CharField(
		_('Gender'),
		choices=GENDERS,
		default='M',
		max_length=3
	)
	joined_on = models.DateTimeField(_('Date joined'), auto_now_add=True, editable=False)
	is_superuser = models.BooleanField(default=False)
	# Staff in company(website)
	is_staff = models.BooleanField(default=False)   
	# Site moderator
	is_mod = models.BooleanField(default=False)  
	# Can user login ? set to False by default since user has to confirm email address...
	is_active = models.BooleanField(default=False)  
	# Is the user a Verified user?
	is_verified = models.BooleanField(default=False)
	is_premium = models.BooleanField(default=False)
	verified_on = models.DateTimeField(null=True, blank=True, editable=False)
	deactivated_on = models.DateTimeField(null=True, blank=True, editable=False)

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

	USERNAME_FIELD = 'username'
	# USERNAME_FIELD and password are required by default
	REQUIRED_FIELDS = ['display_name']   

	objects = UserManager()
	# active = ActiveUserManager()
	# moderators = ModeratorManager()
	# staff = StaffManager()
	# premium = PremiumUserManager()
	# verified = VerifiedUserManager()

	class Meta:
		db_table = 'accounts\".\"user'
		constraints = [
			models.UniqueConstraint(
				fields=['username'],
				name='unique_username',
				include=['display_name']
			)
		]
	
	@classmethod
	def active_users(cls):
		return cls.objects.filter(is_active=True)

	@classmethod
	def premium_users(cls):
		return cls.objects.filter(is_premium=True)

	@classmethod
	def verified_users(cls):
		return cls.objects.filter(is_verified=True)

	def __str__(self):
		return f'{self.display_name}, @{self.username}'

	@property
	def is_suspended(self):
		pass

	def save(self, *args, **kwargs):
		# Title case display_name
		if not self.pk:
			self.display_name = self.display_name.title()
		super().save(*args, **kwargs)

	def delete(self, *args, **kwargs):
		really_delete = kwargs.pop('really_delete', False)

		if really_delete:
			return super().delete(*args, **kwargs) 
		else:
			self.deactivate()
			
	def get_absolute_url(self):
		pass


class UserBlocking(models.Model):
	blocker = models.ForeignKey(
		User,
		db_column='blocker_user_id',
		on_delete=models.CASCADE,
		related_name='+'
	)
	blocked = models.ForeignKey(
		User,
		db_column='blocked_user_id',
		on_delete=models.CASCADE,
		related_name='+'
	)
	blocked_on = models.DateTimeField(auto_now_add=True, editable=False)

	class Meta:
		db_table = 'accounts\".\"user_blocking'
		constraints = [
			models.UniqueConstraint(
				fields=['blocker', 'blocked'],
				name='unique_user_blocking'
			),
		]


class UserFollow(models.Model):
	follower = models.ForeignKey(
		User,
		db_column='follower_user_id',
		on_delete=models.CASCADE,
		related_name='+'
	)
	following = models.ForeignKey(
		User,
		db_column='followed_user_id',
		on_delete=models.CASCADE,
		related_name='+'
	)
	followed_on = models.DateTimeField(auto_now_add=True, editable=False)

	class Meta:
		db_table = 'accounts\".\"user_follow'
		constraints = [
			models.UniqueConstraint(
				fields=['follower', 'following'],
				name='unique_user_follow'
			),
		]


class Suspension(models.Model):
	# Remember only staff can add suspension
	user = models.ForeignKey(
		User, 
		db_column='user_id', 
		on_delete=models.CASCADE,
		related_name='suspensions',
		related_query_name='suspension'
	)
	suspended_on = models.DateTimeField(auto_now_add=True)
	period = models.DurationField(default=datetime.timedelta(days=1))
	over_on = models.DateTimeField()

	@property
	def is_active(self):
		return self.over_on > timezone.now()

	def save(self, *args, **kwargs):
		if not self.pk:
			self.over_on = self.suspended_on + self.period

		super().save(*args, **kwargs)

	class Meta:
		db_table = 'accounts\".\"suspension'


class Settings(models.Model):
	user = models.OneToOneField(
		User, 
		db_column='user_id',
		on_delete=models.CASCADE,
		related_name='settings',
		related_query_name='settings'
	)
	notification_settings = models.JSONField(default=dict)
	site_settings = models.JSONField(default=dict)
	mentions_settings = models.JSONField(default=dict)
	email_settings = models.JSONField(default=dict)

	class Meta:
		db_table = 'accounts\".\"settings'


