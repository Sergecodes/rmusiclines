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

