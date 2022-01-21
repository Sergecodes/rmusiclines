from django.core.exceptions import ValidationError
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from accounts.constants import USERNAME_CHANGE_WAIT_PERIOD
from .models.users.models import User, Suspension


@receiver(pre_save, sender=User)
def parse_email(sender, instance, **kwargs):
    """
	Convert email to lowercase before saving and replace 'googlemail' to 'gmail'.
	See https://mailigen.com/blog/does-capitalization-matter-in-email-addresses/
	"""
    instance.email = instance.email.lower().replace('googlemail', 'gmail')


@receiver(pre_save, sender=User)
def check_username_change(sender, instance, **kwargs):
    """
    Verify if user is about to change his username 
    and if he has the permission to do it.
    """
    # Note that update_fields will always be in kwargs since it is a part of the 
    # function parameters, but it will be None(it won't be an empty list )
    # if it does not contain any fields.
    # So if the field is None, set it to an empty list
    update_fields = kwargs.get('update_fields')
    if not update_fields:
        update_fields = []

    # If username is about to be updated, verify
    # if he is permitted to change his username
    if 'username' in update_fields:
        if not instance.can_change_username:
            raise ValidationError(
				_(
					"You cannot change your username until the %s; "
					"you need to wait %s days after changing your username."
					%(
                        str(instance.can_change_username_until_date), 
                        str(USERNAME_CHANGE_WAIT_PERIOD)
                    )
				)
			)


@receiver(pre_delete, sender=User)
def deactivate_user(sender, instance, **kwargs):
    really_delete = kwargs.pop('really_delete', False)

    if not really_delete:
        instance.deactivate()


@receiver(pre_delete, sender=Suspension)
def end_suspension(sender, instance, **kwargs):
    """End a user's expired(completed) suspension."""
    really_delete = kwargs.pop('really_delete', False)

    if not really_delete:
        instance.end()
