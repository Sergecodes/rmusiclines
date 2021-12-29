"""Contains project-wide utilities"""

from django.contrib.contenttypes.models import ContentType


class UsesCustomSignal:
    """
    Dummy Mixin used on a model to show that it has a custom signal attached.
    This is used to facilitate debugging...
    """
    pass


def get_content_type(model_obj):
    """Return the content type of a given model"""
    return ContentType.objects.get_for_model(model_obj)

