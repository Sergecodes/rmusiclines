"""Contains project-wide utilities"""

import base64
import graphene
from graphene_django.converter import convert_django_field
from taggit.managers import TaggableManager


class UsesCustomSignal:
    """
    Dummy Mixin used on a model to show that it has a custom signal attached.
    This is used to facilitate debugging...
    """
    pass


class GraphenePKMixin:
    """
    Use with a graphene ObjectType to include pk of the model in fields
    since relay overshadows the object's id with a global ID
    """
    pk = graphene.Field(graphene.Int, source='pk')


class GraphenePhotoMixin:
    """
    Used with DjangoObjectTypes that represent a photo model.
    Used to query base64 string and url
    """
    base64_str = graphene.String()
    url = graphene.String()

    def resolve_base64_str(root, info):
        # root is the model object type that is in context
        return base64.b64encode(root.photo.read()).decode('utf-8')

    def resolve_url(root, info):
        return root.photo.url


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

