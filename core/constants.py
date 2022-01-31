"""Project-wide constants"""

from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _


GENDERS = (
    ('M', _('Male')),
    ('F', _('Female')),
    ('N/B', _('Non-binary'))
)

FILE_STORAGE_CLASS = import_string(settings.DEFAULT_FILE_STORAGE)


## SESSION KEYS FORMAT
# `user-{foo}-new-email` which will point to the value of the user with username 'foo' 's new email.
# This is set when changing the user's email in the user's ChangeEmailMutation
# Notice we use hyphens(instead of possibly underscores) coz underscores are valid characters
# in a username.
#
#
