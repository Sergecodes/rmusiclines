import graphene
from django.utils.translation import gettext_lazy as _
from graphene_django import DjangoObjectType
from accounts.models.artists.models import Artist
from core.utils import PKMixin, GrapheneRenderTaggitTags


class ArtistNode(PKMixin, GrapheneRenderTaggitTags, DjangoObjectType):
    class Meta:
        model = Artist
        interfaces = [graphene.relay.Node, ]

