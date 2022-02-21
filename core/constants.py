"""Project-wide constants"""

from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _


# class ImageFormForChoice(models.TextChoices):
#     """Enum for image form choices"""
#     ARTIST_PHOTO = 'artist_photo', _('Artist photo')
#     ARTIST_POST_PHOTO = 'artist_post_photo', _('Artist post photo')
#     NON_ARTIST_POST_PHOTO = 'non_artist_post_photo', _('Non artist post photo')
#     PROFILE_PICTURE = 'profile_picture', _('Profile picture')
#     COVER_PHOTO = 'cover_photo', _('Cover photo')


GENDERS = (
    ('M', _('Male')),
    ('F', _('Female')),
    ('N/B', _('Non-binary'))
)

FILE_STORAGE_CLASS = import_string(settings.DEFAULT_FILE_STORAGE)



## SESSION KEYS FORMAT


## CACHE KEYS FORMAT
# `{username}-new-email` which will point to the value of the user (username)'s new email.
# This is set when changing the user's email in the user's ChangeEmailMutation
# (SendNewEmailActivationMixin).
# Notice we use hyphens(instead of possibly underscores) coz underscores are valid characters
# in a username.  ** Sessions are not used to store new email because the user may use 
# an email that is in a different phone, or basically they may use another browser 
# to open the new email activation link, thus the session will be different. So store the email in 
# cache.
#
#
# `{user.username}-unposted-photos` which is a list containing a dict with keys filename, file_bytes,
# mimetype. This list is a list of photos that have been uploaded but not yet posted under a post. 
# 
#
# `{user.username}-unposted-video` which is a dict with keys filename, url, mimetype.
# This dict contains video that has been uploaded but not yet posted under a post
#
#
#

