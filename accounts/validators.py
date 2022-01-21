# from django.core.exceptions import ValidationError

from django.contrib.auth.password_validation import  UserAttributeSimilarityValidator
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


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
		

