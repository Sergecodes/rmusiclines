from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models.users.models import User, Suspension


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
