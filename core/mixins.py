"""Contains project-wide utilities"""

import graphene
from graphene_django.converter import convert_django_field
from taggit.managers import TaggableManager


class UsesCustomSignal:
    """
    Dummy Mixin used on a model to show that it has a custom signal attached.
    This is used to facilitate debugging...
    """
    pass


class PKMixin:
    """
    Use with a graphene ObjectType to include pk of the model in fields
    since relay overshadows the object's id with a global ID
    """
    pk = graphene.Field(type=graphene.Int, source='pk')


class GrapheneRenderTaggitTags:
    """
    Use this mixin to enable graphene-django correctly render django-taggit 
    tags (as a list of strings).
    The corresponding model of the graphene type using this mixin should have a property
    `get_tags` that returns the tags of the model (eg obj.tags.all())
    """

    # Make django-taggit's TaggableManager interpretable to graphene
    @convert_django_field.register(TaggableManager)
    def convert_field_to_string(field, registry=None):
        print(field)
        print("in graphene render tags")
        return graphene.List(graphene.String, source='get_tags')

