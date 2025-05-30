# fidzic.com...

# python-decouple
# See https://pypi.org/project/python-decouple/  
# and https://simpleisbetterthancomplex.com/2015/11/26/
# package-of-the-week-python-decouple.html

from datetime import timedelta
from decouple import config, Csv
from django.utils.translation import gettext_lazy as _
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

AUTH_USER_MODEL = 'accounts.User'

# Required since we use the django.contrib.sites app
SITE_ID = 1

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
SECRET_KEY = config('SECRET_KEY')
USE_CONSOLE_EMAIL = config('USE_CONSOLE_EMAIL', default=True, cast=bool)

# DB
USE_PROD_DB = config('USE_PROD_DB', cast=bool)
DB_USER = config('DB_USER')
DB_NAME = config('DB_NAME')
DB_PASSWORD = config('DB_PASSWORD')
DB_HOST = config('DB_HOST')
DB_PORT = config('DB_PORT')

# AWS
USE_S3 = config('USE_S3', default=False, cast=bool)
USE_AWS_VIDEO_ENCODER = config('USE_AWS_VIDEO_ENCODER')
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')

# Misc
CONTENT_IS_FLAGGED_COUNT = config('CONTENT_IS_FLAGGED_COUNT', cast=int)
USER_IS_FLAGGED_COUNT = config('USER_IS_FLAGGED_COUNT', cast=int)
AUTO_DELETE_FLAGS_COUNT = config('AUTO_DELETE_FLAGS_COUNT', cast=int)
AUTO_SUSPEND_USER_ACCOUNT_FLAGS_COUNT = config('AUTO_SUSPEND_USER_ACCOUNT_FLAGS_COUNT', cast=int)


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

if USE_PROD_DB:
	pass
else:
	DATABASES = {
		# Configure database with schemas
		'default': {
			'ENGINE': 'django.db.backends.postgresql_psycopg2',
			'OPTIONS': {
				# Use `django` schema so as not to polute public schema
				'options': '-c search_path=django,public'
			},
			'NAME': DB_NAME,
			'USER': DB_USER,
			'PASSWORD': DB_PASSWORD,
			'HOST': DB_HOST,
			'PORT': DB_PORT,
		},
		'accounts': {
			'ENGINE': 'django.db.backends.postgresql_psycopg2',
			'OPTIONS': {
				'options': '-c search_path=accounts,public'
			},
			'NAME': DB_NAME,
			'USER': DB_USER,
			'PASSWORD': DB_PASSWORD,
			'HOST': DB_HOST,
			'PORT': DB_PORT,
		},
		'posts': {
			'ENGINE': 'django.db.backends.postgresql_psycopg2',
			'OPTIONS': {
				'options': '-c search_path=posts,public'
			},
			'NAME': DB_NAME,
			'USER': DB_USER,
			'PASSWORD': DB_PASSWORD,
			'HOST': DB_HOST,
			'PORT': DB_PORT,
		},
		'notifications': {
			'ENGINE': 'django.db.backends.postgresql_psycopg2',
			'OPTIONS': {
				'options': '-c search_path=notifications,public'
			},
			'NAME': DB_NAME,
			'USER': DB_USER,
			'PASSWORD': DB_PASSWORD,
			'HOST': DB_HOST,
			'PORT': DB_PORT,
		},
		'flagging': {
			'ENGINE': 'django.db.backends.postgresql_psycopg2',
			'OPTIONS': {
				'options': '-c search_path=flagging,public'
			},
			'NAME': DB_NAME,
			'USER': DB_USER,
			'PASSWORD': DB_PASSWORD,
			'HOST': DB_HOST,
			'PORT': DB_PORT,
		},
		'subscriptions': {
			'ENGINE': 'django.db.backends.postgresql_psycopg2',
			'OPTIONS': {
				'options': '-c search_path=subscriptions,public'
			},
			'NAME': DB_NAME,
			'USER': DB_USER,
			'PASSWORD': DB_PASSWORD,
			'HOST': DB_HOST,
			'PORT': DB_PORT,
		}
	}

# EMAIL_HOST = config('EMAIL_HOST', default='localhost')
# EMAIL_PORT = config('EMAIL_PORT', default=25, cast=int)
# EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
# EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
# EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)

if DEBUG:
	EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Application definition

INSTALLED_APPS = [
	# django-grappelli should be placed before django.contrib.admin
	'grappelli',
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	# Required by django-allauth and django-activity-stream
	'django.contrib.sites',  

	# Third-party apps
	'allauth',
	'allauth.account',
	'allauth.socialaccount',
	'allauth.socialaccount.providers.apple',
	'allauth.socialaccount.providers.facebook',
	'allauth.socialaccount.providers.google',
	'allauth.socialaccount.providers.spotify',
	'django_extensions',
	'django_filters',
	'easy_thumbnails',
	'graphene_django',
	'graphql_auth',
	'graphql_jwt.refresh_token.apps.RefreshTokenConfig',
	'paypal.standard.ipn',
	'taggit_serializer',

	# Project apps
	'accounts',
	'core',
	'posts',
	'flagging',
	'notifications',
	'subscriptions',

	# Should be the last (come after apps that can generate activities)
	'actstream',
]

MIDDLEWARE = [
	'django.middleware.security.SecurityMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rml.urls'

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				'django.template.context_processors.debug',
				'django.template.context_processors.request',
				'django.contrib.auth.context_processors.auth',
				'django.contrib.messages.context_processors.messages',
			],
		},
	},
]

WSGI_APPLICATION = 'rml.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTHENTICATION_BACKENDS = [
	# Needed to login by username in Django admin, regardless of 'allauth'
	'django.contrib.auth.backends.ModelBackend',

	# Enable authentication using graphql_auth which implicitly uses graphql_jwt
	'graphql_auth.backends.GraphQLAuthBackend',

	# 'allauth' specific authentication methods, such as login by e-mail
	'allauth.account.auth_backends.AuthenticationBackend'
]


AUTH_PASSWORD_VALIDATORS = [
	{
		'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
	},
	# Custom validators
	{
		'NAME': 'accounts.validators.UserDisplayNameSimilarityPasswordValidator',
	},
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [
	BASE_DIR / 'locale',
]

# LOGIN_URL = reverse_lazy('accounts:login')
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


# Caching TODO use memcached in production!! (even before production!)
# (it is the best cache backend that django supports)
CACHES = {
	'default': {
		'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
		'TIMEOUT': 300,  # The default(300s = 5mins)
		# 'TIMEOUT': 60 * 60 * 24,  # 86400(s)=24h
	}
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
if USE_S3:
	AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
	AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
	AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
	AWS_S3_SIGNATURE_VERSION = 's3v4'
	AWS_S3_REGION_NAME = 'us-east-1'
	AWS_S3_FILE_OVERWRITE = False
	AWS_DEFAULT_ACL = None
	AWS_S3_VERIFY = True

	## Note: Variables ending in '_' are user-defined, not required or used by a package
	AWS_S3_CUSTOM_DOMAIN_ = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
	AWS_S3_OBJECT_PARAMETERS = {
		# use a high value so that files are cached for long (6months=2628000)
		# however, updates on files won't work ... and file name  should be changed after updates..
		# for now, set it to 1 day(86400secs)
		# 1month = 2.628e+6 (2628000secs)
		'CacheControl': 'max-age=86400'
	}
	# s3 static settings
	# STATIC_LOCATION_ = 'static'
	STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN_}/static/'
	STATICFILES_STORAGE = 'core.storages.StaticStorage'
	STATIC_ROOT = 'staticfiles/'
	# We don't need STATIC_URL here since to upload files, we'll run collectstatic
	# and all static files will be placed in the STATIC_ROOT folder

	# s3 public media settings. 
	# This var is also used in core.storages to set the location of media files
	PUBLIC_MEDIA_LOCATION_ = 'media'
	MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN_}/{PUBLIC_MEDIA_LOCATION_}/'
	MEDIA_ROOT = MEDIA_URL
	DEFAULT_FILE_STORAGE = 'core.storages.PublicMediaStorage'

	# # s3 private media settings
	# PRIVATE_MEDIA_LOCATION = 'private'
	# PRIVATE_FILE_STORAGE = 'core.storages.PrivateMediaStorage'
else:
	DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'  
	STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
	STATIC_URL = 'static/'
	STATIC_ROOT = BASE_DIR / 'staticfiles'
	# STATICFILES_DIRS = [
	# 	BASE_DIR / 'static'
	# ]

	MEDIA_URL = 'media/'
	MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Use this to configure the test databases and schema during first run.
# TEST_RUNNER = 'core.tests.runner.PostgresSchemaTestRunner'


### Third-party apps settings
## allauth settings (https://django-allauth.readthedocs.io/en/latest/configuration.html)
SOCIALACCOUNT_PROVIDERS = {
	'apple': {
		'VERIFIED_EMAIL': True
	},
	'facebook': {

	},
	'google': {
		# 'VERIFIED_EMAIL': True
	},
	'spotify': {
		# 'VERIFIED_EMAIL': True
	}
}

ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_CONFIRMATION_COOLDOWN = 300  
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_SESSION_REMEMBER = False
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_USERNAME_BLACKLIST = [
	'Admin', 'Fidzic', 'Staff'
]
ACCOUNT_USER_DISPLAY = 'accounts.User.__str__'


## django-activity-stream
ACTSTREAM_SETTINGS = {
	'MANAGER': 'core.managers.ActionManager',
	'USE_JSONFIELD': False
}


## django-grappelli
GRAPPELLI_ADMIN_TITLE = 'FIDZIC MUSIC SITE'
GRAPPELLI_AUTOCOMPLETE_SEARCH_FIELDS = {
	'accounts': {
		'User': ('id__exact', 'username__contains', 'display_name__icontains', ),
		'Artist': ('id__exact', 'name__icontains', ),
		'ArtistTag': ('id__iexact', 'name__icontains', ), 
	},
	'posts': {
		'ArtistPost': ('uuid__iexact', 'body__icontains', ),
		'NonArtistPost': ('uuid__iexact', 'body__icontains', ),
		'PostHashtag': ('id__iexact', 'topic__icontains', )
	},

}


## django-taggit ##
# TAGGIT_CASE_INSENSITIVE = True


## django-paypal settings
# https://overiq.com/django-paypal/, 
# https://django-paypal.readthedocs.io/en/stable/overview.html


## easy_thumbnails ##
THUMBNAIL_ALIASES = {
	# width and height are required for size
	'': {
		'thumb': {'size': (800, 800)},
		'sm_thumb': {'size': (500, 500)},
		'profile_pic': {'size': (400, 400)},
		'cover_photo': {'size': (600, 250)},
		'artist_photo': {'size': (900, 900)}
	}
}
THUMBNAIL_CACHE_DIMENSIONS = True
THUMBNAIL_DEBUG = DEBUG
THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE
THUMBNAIL_SUBDIR = 'thumbs'
# THUMBNAIL_WIDGET_OPTIONS = {}


## graphene_django ##
GRAPHENE = {
    'SCHEMA': 'core.graphql.schema.schema',
	'ATOMIC_MUTATION': True,
	'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
		# For debugging
		'graphene_django.debug.DjangoDebugMiddleware'
    ],
	'DJANGO_CHOICE_FIELD_ENUM_V3_NAMING': True,
	# 'DJANGO_CHOICE_FIELD_ENUM_CUSTOM_NAME': 'core.utils.graphene_enum_naming',

}


## graphql_auth ##
GRAPHQL_AUTH = {
    'LOGIN_ALLOWED_FIELDS': ['email', 'username'],
    'ALLOW_LOGIN_NOT_VERIFIED': False,
	'REGISTER_MUTATION_FIELDS': {
		'email': 'String',
		'username': 'String',
		'display_name': 'String',
		'country': 'String',
		'birth_date': 'Date',
	},
	'REGISTER_MUTATION_FIELDS_OPTIONAL': {
		'bio': 'String',
		'gender': 'String', 
	},
	'UPDATE_MUTATION_FIELDS': [],
	# 'UPDATE_MUTATION_FIELDS': {
	# 	'display_name': 'String',
	# 	'country': 'String',
	# 	'birth_date': 'Date',
	# 	'gender': 'String', 
	# 	'bio': 'String',
	# },
	'USER_NODE_FILTER_FIELDS': {
		'email': ['exact', ],
		'username': ['exact', 'icontains', 'istartswith'],
		'is_active': ['exact'],
		'type__is_verified': ['exact'],
		'type__is_premium': ['exact'],
		'type__is_mod': ['exact'],
		# 'status__archived': ['exact'],
		# 'status__verified': ['exact'],
		# 'status__secondary_email': ['exact'],
		
	}
}


## graphql_jwt ##
GRAPHQL_JWT = {
    "JWT_VERIFY_EXPIRATION": True,
    "JWT_LONG_RUNNING_REFRESH_TOKEN": True,
	"JWT_EXPIRATION_DELTA": timedelta(days=3),
    "JWT_REFRESH_EXPIRATION_DELTA": timedelta(days=7),
	"JWT_ALLOW_ANY_CLASSES": [
        "graphql_auth.relay.Register",
        "graphql_auth.relay.VerifyAccount",
        "graphql_auth.relay.ResendActivationEmail",
        "graphql_auth.relay.SendPasswordResetEmail",
        "graphql_auth.relay.PasswordReset",
        "graphql_auth.relay.ObtainJSONWebToken",
        "graphql_auth.relay.VerifyToken",
        "graphql_auth.relay.RefreshToken",
        "graphql_auth.relay.RevokeToken",
        # "graphql_auth.relay.VerifySecondaryEmail",
    ],
}



