import datetime
from django_countries.fields import CountryField
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.utils.functional import cached_property, classproperty
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.fields import ThumbnailerImageField

from accounts.constants import (
    USER_MIN_AGE, USER_MAX_AGE, USERS_COVER_PHOTOS_UPLOAD_DIR, 
    USERS_PROFILE_PICTURES_UPLOAD_DIR, USERNAME_CHANGE_WAIT_PERIOD, 
    NON_PREMIUM_USER_MAX_DOWNLOADS_PER_MONTH,
)
from accounts.managers import UserManager
from accounts.utils import get_age
from accounts.validators import UserUsernameValidator, validate_profile_and_cover_photo
from core.constants import GENDERS, FILE_STORAGE_CLASS
from core.mixins import UsesCustomSignal
from posts.models.artist_posts.models import ArtistPost
from posts.models.non_artist_posts.models import NonArtistPost
from .operations import UserOperations, SuspensionOperations



def profile_pic_upload_path(user, filename):
    # File will be uploaded to MEDIA_ROOT/users/user_<id>/profile_pics/<filename>
    return 'users/user_{0}/{1}/{2}'.format(
		user.pk, 
		USERS_PROFILE_PICTURES_UPLOAD_DIR,
		filename
	)


def cover_photo_upload_path(user, filename):
    # File will be uploaded to MEDIA_ROOT/user_<id>/cover_photos/<filename>
    return 'users/user_{0}/{1}/{2}'.format(
		user.pk, 
		USERS_COVER_PHOTOS_UPLOAD_DIR,
		filename
	)


class UserType(models.Model):
    """
    Model used to store different user types(premium, verified, moderator, site_agent).
    """

    user = models.OneToOneField(
        'User', 
        on_delete=models.CASCADE, 
        related_name='type',
        db_column='user_id',
		primary_key=True
    )
    is_mod = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    # Site agents will be like dummy users that will post content on the site, 
    # basically to give the impression that many people are using the site.
    # Some of these accounts can even be verified :)
    is_site_agent = models.BooleanField(default=False)

    def __str__(self):
        return "%s - type" % (self.user)

    class Meta:
        db_table = 'accounts\".\"user_type'
        indexes = [
            models.Index(
				fields=['is_mod'], 
				name='user_type_is_mod_idx'
			),
            models.Index(
				fields=['is_verified'], 
				name='user_type_is_verified_idx'
			),
            models.Index(
				fields=['is_premium'], 
				name='user_type_is_premium_idx'
			),
		]


class User(AbstractBaseUser, PermissionsMixin, UserOperations, UsesCustomSignal):
    username_validator = UserUsernameValidator()

    username = models.CharField(
        _('Username'),
        max_length=15,
        # Enforce uniqueness via UniqueConstraint on Meta class
        validators=[username_validator],
        help_text=_(
            'Your username should be less than 15 characters '
            'and may contain only letters, numbers and underscores; '
            'no other chareacters are allowed.'
        ),
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
    email = models.EmailField(
        _('Email address'),
        max_length=50,
        help_text=_('We will send a verification code to this email'),
        error_messages={
            'unique': _('A user with that email already exists.'),
            # null, blank, invalid, invalid_choice, unique, unique_for_date
        }
    )
    display_name = models.CharField(_('Full name'), max_length=50)
    country = CountryField(verbose_name=_('Location'), blank_label=_('(select country)'))
    birth_date = models.DateField(_('Date of birth'))
    bio = models.CharField(
        _('Bio'), 
        max_length=150, 
        blank=True,
        help_text=_(
            'Write about yourself & taste for music. '
            'You may include your favorite artists or songs.'
        )
    )
    profile_picture = ThumbnailerImageField(
        thumbnail_storage=FILE_STORAGE_CLASS(), 
        upload_to=profile_pic_upload_path,
		resize_source=dict(size=(400, 400)),
        validators=[FileExtensionValidator(['png, jpg']), validate_profile_and_cover_photo],
        width_field='profile_picture_width', 
        height_field='profile_picture_height',
        # no null=True needed, since this translates to a char field 
        # and char fields don't need it..
        blank=True  
    )
    cover_photo = ThumbnailerImageField(
        thumbnail_storage=FILE_STORAGE_CLASS(), 
        upload_to=cover_photo_upload_path,
		resize_source=dict(size=(600, 250)),
        validators=[FileExtensionValidator(['png, jpg'])],
        width_field='cover_photo_width',
        height_field='cover_photo_height',
        blank=True  
    )
    # Django specific optimizations for getting width and height of images
    profile_picture_width = models.PositiveIntegerField(default=0)
    profile_picture_height = models.PositiveIntegerField(default=0)
    cover_photo_width = models.PositiveIntegerField(default=0)
    cover_photo_height = models.PositiveIntegerField(default=0)

    gender = models.CharField(choices=GENDERS, default='M', max_length=3)

    # From django's AbstractUser model and used joined_on and not date_joined
    # Staff or admin (can login to admin panel)
    is_staff = models.BooleanField(default=False)   
    
    # Can user login ? set to False by default since user has to confirm email address...
    is_active = models.BooleanField(default=False)  
    joined_on = models.DateTimeField(_('Date joined'), auto_now_add=True, editable=False)

    verified_on = models.DateTimeField(null=True, blank=True, editable=False)
    deactivated_on = models.DateTimeField(null=True, blank=True, editable=False)
    last_changed_username_on = models.DateTimeField(null=True, blank=True, editable=False)

    # From the PermissionsMixin class, just to update related_name attribute of m2m fields
    is_superuser = models.BooleanField(default=False)
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='users',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='users',
        related_query_name='user',
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
        symmetrical=False
    )

    # Post related info
    pinned_artist_post = models.OneToOneField(
        ArtistPost,
        related_name='+',
        db_column='pinned_artist_post_id',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    pinned_non_artist_post = models.OneToOneField(
        NonArtistPost,
        related_name='+',
        db_column='pinned_non_artist_post_id',
        on_delete=models.CASCADE,
        blank=True, 
        null=True
    )
    num_followers = models.PositiveIntegerField(default=0, editable=False)
    num_following = models.PositiveIntegerField(default=0, editable=False)
    num_artist_posts = models.PositiveIntegerField(default=0, editable=False)
    num_non_artist_posts = models.PositiveIntegerField(default=0, editable=False)
    num_artist_post_reposts = models.PositiveIntegerField(default=0, editable=False)
    num_non_artist_post_reposts = models.PositiveIntegerField(default=0, editable=False)
    num_ancestor_artist_post_comments = models.PositiveIntegerField(default=0, editable=False)
    num_ancestor_non_artist_post_comments = models.PositiveIntegerField(default=0, editable=False)


    # EMAIL_FIELD isn't normally compulsory but in our case it needs to be set for graphql-auth
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    # USERNAME_FIELD and password are required by default
    REQUIRED_FIELDS = ['display_name']   

    objects = UserManager()
    # active = ActiveUserManager()
    # moderators = ModeratorManager()
    # staff = StaffManager()
    # premium = PremiumUserManager()
    # verified = VerifiedUserManager()

    def __str__(self):
        return f'{self.display_name}, @{self.username}'

    @classproperty
    def superuser(cls):
        return cls.objects.get(superuser=True)

    @classproperty
    def main_site_account(cls):
        # TODO Create a principal site account and update this
        return cls.superuser

    @classproperty
    def site_services_account(cls):
        # TODO Create this account. It will be responsible for instance for 
        # notifying users if needed; such as when their account if flagged...
        return cls.superuser

    @classproperty
    def moderators(cls):
        return cls.objects.filter(type__is_mod=True)

    @classproperty
    def staff(cls):
        return cls.objects.filter(is_staff=True)

    @classproperty
    def active_users(cls):
        return cls.objects.filter(is_active=True)

    @classproperty
    def premium_users(cls):
        return cls.objects.filter(type__is_premium=True)

    @classproperty
    def verified_users(cls):
        return cls.objects.filter(type__is_verified=True)

    @cached_property
    def is_mod(self):
        return self.type.is_mod

    @cached_property
    def is_verified(self):
        return self.type.is_verified

    @property
    def is_premium(self):
        return self.type.is_premium

    @property
    def status_verified(self):
        """
        Graphql auth uses a custom model UserStatus to track status of users.
        This property get the status of a user.
        """
        # Import here to prevent circular import errors
        from graphql_auth.models import UserStatus

        try:
            return self.status.verified
        except AttributeError:
            status = UserStatus.objects.create(user=self, verified=self.is_active)
            return status.verified

    @property
    def can_change_username(self):
        """Determine if the user is permitted to change his username."""
        last_changed_on = self.last_changed_username_on

        # If this field is null, then user has never changed their username
        # thus they are permitted to change it.
        if not last_changed_on:
            return True

        # Else if user has already changed his username, check if he has
        # permission to change it.
        if timezone.now() > last_changed_on + USERNAME_CHANGE_WAIT_PERIOD:
            return True
        else:
            return False

    @property 
    def can_change_username_until_date(self):
        """Get the minimum date on which user can change his username."""
        return self.last_changed_username_on + USERNAME_CHANGE_WAIT_PERIOD

    @property
    def can_download(self):
        """Return whether or not a user can download posts."""
        # Premium users and superuser can download any number of posts
        if self.is_premium or self.is_superuser:
            return True
        
        # Verify if user has reached monthly download limit
        now = timezone.now()
        current_month, current_year = now.month, now.year
        current_num_downloads = self.num_downloads(current_month, current_year)

        if current_num_downloads == NON_PREMIUM_USER_MAX_DOWNLOADS_PER_MONTH:
            return False
        else:
            return True

    @property
    def age(self):
        return get_age(self.birth_date)

    @property
    def is_suspended(self):
        return self.suspensions.filter(over_on__gte=timezone.now()).exists()

    @property
    def private_artist_posts(self):
        return self.artist_posts.filter(is_private=True)

    @property
    def private_non_artist_posts(self):
        return self.non_artist_posts.filter(is_private=True)

    @property
    def public_artist_posts(self):
        return self.artist_posts.filter(is_private=False)

    @property
    def public_non_artist_posts(self):
        return self.non_artist_posts.filter(is_private=False)

    @property
    def parent_artist_post_comments(self):
        return self.overall_artist_post_comments.filter(is_parent=True)

    @property
    def parent_non_artist_post_comments(self):
        return self.overall_non_artist_post_comments.filter(is_parent=True)
       
    def clean(self):
        # This is the default construct of the AbstractUser class; calling the super() method
        # and setting the email to a nomalized one.
        # The super method basically calls the AbstractBaseUser class' clean() method
        # which normalizes the username; despite the fact that hovering over this method
        # doesn't lead to the AbstractBaseUser class' implementation 
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

        # Don't allow both pinned artist post and pinned non artist post
        if self.pinned_artist_post and self.pinned_non_artist_post:
            raise ValidationError(
                _(
                    "Both an artist post and a non artist post can't be pinned "
                    "(you can pin only one post)."
                ),
                code='multiple_post_pin'
            )

        # Only accept users older than 13(ref. COPPA) 
        # and younger than 120 (in 2021, oldest person alive is 118).
        if self.age < USER_MIN_AGE: 
            raise ValidationError(
                _("You need to be at least 13 years old to create an account."),
                code='not_old_enough'
            )

        if self.age > USER_MAX_AGE: 
            raise ValidationError(
                _("Come on, you can't be that old."),
                code='too_old'
            ) 

    def save(self, *args, **kwargs):
        # See https://stackoverflow.com/q/4441539/
        # why-doesnt-djangos-model-save-call-full-clean/
        self.clean()
        super().save(*args, **kwargs)
            
    def get_absolute_url(self):
        pass

    class Meta:
        db_table = 'accounts\".\"user'
		# Index names cannot be longer than 30 characters.
        indexes = [
			models.Index(
				fields=['is_superuser'], 
				name='user_is_superuser_idx'
			),
            models.Index(
				fields=['is_staff'], 
				name='user_is_staff_idx'
			),
            models.Index(
				fields=['is_active'], 
				name='user_is_active_idx'
			),
		]
        constraints = [
            models.UniqueConstraint(
                fields=['username'],
                include=['display_name'],
                name='unique_username'
            ),
            models.UniqueConstraint(
                fields=['email'],
                # Apply unique constraint on email only when the user is active.
                # This prevents someone from for instance creating accounts with people's
                # email adresses.
                condition=Q(is_active=True),
                name='unique_active_email'
            )
            ## Check constraint on table:
            # ALTER TABLE accounts.artist ADD CONSTRAINT "age_gte_13_and_lte_120" CHECK (
            # 	birth_date <= (now()::date - '15 years'::interval) AND 
            # 	birth_date >= (now()::date - '100 years'::interval)
            # )
            #
            # It can't be set here due to the now() function been used,

            ## TRIGGER for pinning post set on table.
            #
        ]
    

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

    def __str__(self):
        return f'{str(self.blocker)} blocks {str(self.blocked)}'

    def clean(self):
        if self.blocker == self.blocked:
            raise ValidationError(
                _("You can't block yourself."),
                code="can't_block_self"
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        

    class Meta:
        db_table = 'accounts\".\"user_blocking'
        constraints = [
            models.UniqueConstraint(
                fields=['blocker', 'blocked'],
                name='unique_user_blocking'
            ),
            ## User can't block themself
            models.CheckConstraint(
                check=~Q(blocker=F('blocked')),
                name='cannot_block_self'
            )
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

    def __str__(self):
        return f'{str(self.follower)} follows {str(self.following)}'

    def clean(self):
        if self.follower == self.following:
            raise ValidationError(
                _("You can't follow yourself."),
                code="can't_follow_self"
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'accounts\".\"user_follow'
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'following'],
                name='unique_user_follow'
            ),
            ## User can't follow themself
            models.CheckConstraint(
                check=~Q(follower=F('following')),
                name='cannot_follow_self'
            )
        ]


class Suspension(models.Model, SuspensionOperations, UsesCustomSignal):

    # Remember only staff can add suspension
    suspender = models.ForeignKey(
        User, 
        db_column='suspender_user_id', 
        on_delete=models.CASCADE,
        related_name='suspended_users',
        related_query_name='suspension'
    )
    suspended_user = models.ForeignKey(
        User, 
        db_column='user_id', 
        on_delete=models.CASCADE,
        related_name='suspensions',
        related_query_name='suspension'
    )
    given_on = models.DateTimeField(auto_now_add=True)
    duration = models.DurationField(default=datetime.timedelta(days=1))
    reason = models.TextField()
    over_on = models.DateTimeField()

    def __str__(self):
        return f'From {self.given_on} to {self.over_on} ({ str(self.period) })'

    @property
    def is_active(self):
        return self.over_on > timezone.now()

    @property
    def time_left(self):
        return self.over_on - timezone.now()

    def clean(self):
        # Staff can't be suspended
        if self.suspended_user.is_staff:
            raise ValidationError(
                _("You can't suspend a staff."),
                code="can't_suspend_staff"
            )

    def save(self, *args, **kwargs):
        self.clean()

        if not self.pk:
            # Since object is still new, given_on has not yet being set (is None)
            self.given_on = timezone.now()
            self.over_on = self.given_on + self.duration

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

    def __str__(self):
        return f"{str(self.user)}'s settings"

    class Meta:
        db_table = 'accounts\".\"settings'
        verbose_name = _('Settings')
        verbose_name_plural = _('Settings')


