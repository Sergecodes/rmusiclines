from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from .models.users.models import User, Suspension


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
        return


@receiver(pre_delete, sender=Suspension)
def end_suspension(sender, instance, **kwargs):
    really_delete = kwargs.pop('really_delete', False)

    if not really_delete:
        instance.end()
        return
