from django.contrib.auth import get_user_model
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from graphql_auth.models import UserStatus
from graphql_auth.signals import user_verified

from accounts.models.users.models import Suspension

User = get_user_model()


@receiver(pre_save, sender=User)
def parse_email(sender, instance, **kwargs):
    """
	Convert email to lowercase before saving and replace 'googlemail' to 'gmail'.
	See https://mailigen.com/blog/does-capitalization-matter-in-email-addresses/
	"""
    instance.email = instance.email.lower().replace('googlemail', 'gmail')


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


@receiver(user_verified, sender=UserStatus)
def mark_user_active(sender, user, **kwargs):
    """Mark user as active after his account is verified using graphql"""
    # kwargs contains just the signal object as a key ({'signal': Signal_object})
    user.is_active = True
    user.save(update_fields=['is_active'])

