from django.contrib.auth.password_validation import  UserAttributeSimilarityValidator
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _

from core.utils import get_file_extension


class UserUsernameValidator(RegexValidator):
	"""
	Username rules:
	- Username should be between 1 to 15 characters.
	- Username should not contain any symbols, dashes or spaces.
	- All other characters are allowed(letters, numbers, and underscores).
	"""
	regex = r'\A[a-zA-Z0-9_]{1,15}\Z'
	# or regex = r'\A[\w]{1,15}\Z'
	message = _(
		'Enter a valid username. This value should contain at most 15 characters. \n '
		'It should not contain any symbols, dashes or spaces; '
		'all other characters are allowed(letters, numbers, and underscores)'
	)
	flags = 0


class UserDisplayNameSimilarityPasswordValidator(UserAttributeSimilarityValidator):
	"""Add user display_name to password similarity check"""
	def __init__(self, *args, **kwargs):
		user_attributes = ['username', 'email', 'display_name']
		super().__init__(user_attributes)
		

def validate_artist_photo(photo_file):
    """
    Validate artist photo
    - Max size: 20mb
    - Types: png, jpg

    :param `photo_file`: File object
    """
    validate_profile_and_cover_photo(photo_file)


def validate_profile_and_cover_photo(photo_file):
    """
    Validate profile pic and cover photo
    - Max size: 20mb
    - Types: png, jpg

    :param `photo_file`: File object
    """
    # TODO Also validate photo on server level(nginx, ...) before sending to django

    MAX_PHOTO_SIZE = 20971520
    VALID_CONTENT_TYPES = ['image/png', 'image/jpg', 'image/jpeg']
    file = photo_file

    try:
        content_type = file.content_type

        if content_type in VALID_CONTENT_TYPES:
            # Verify if content type is same as extension. If it's not the same, that means
            # someone has surely tampered with the file extension(renamed it).
            if content_type in ['image/jpg', 'image/jpeg']:
                ctype_ext = 'jpg'
            else:
                ctype_ext = content_type.split('/')[-1].lower()

            if ctype_ext != get_file_extension(file):
                raise ValidationError(
                    _("Corrupt file, content type doesn't match with extension"),
                    code='corrupt_file'
                )

            if (file_size := file.size) > MAX_PHOTO_SIZE:
                raise ValidationError(
                    _('Please keep filesize under %(max_photo_size)s. Current filesize %(photo_size)s'),
                    code='large_file',
                    params={
                        'max_photo_size': filesizeformat(MAX_PHOTO_SIZE),
                        'photo_size': filesizeformat(file_size)
                    }
                )
        else:
            raise ValidationError(
                _('Filetype %(ctype)s not supported.'),
                code='invalid',
                params={'ctype': content_type}
            )
    except AttributeError:
        pass



