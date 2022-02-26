from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    """To handle site's static files"""
    location = settings.STATIC_ROOT or 'staticfiles/'


class PublicMediaStorage(S3Boto3Storage):
    """
    Storage backend for site's media files(such as artists' photos) 
    and user uploaded files
    """
    location = settings.PUBLIC_MEDIA_LOCATION_ or 'media'
    # eg. Don't overwite files since some users may have files with the same name.
    file_overwrite = False


# class PrivateMediaStorage(S3Boto3Storage):
#     """To handle private media files"""
#     location = 'private'
#     default_acl = 'private'
#     file_overwrite = False
#     custom_domain = False

