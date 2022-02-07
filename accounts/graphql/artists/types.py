import graphene
from graphene_django import DjangoObjectType

from accounts.models.artists.models import Artist, ArtistFollow
from core.utils import PKMixin, GrapheneRenderTaggitTags


class ArtistNode(PKMixin, GrapheneRenderTaggitTags, DjangoObjectType):
    class Meta:
        model = Artist
        interfaces = [graphene.relay.Node, ]


class ArtistFollowNode(PKMixin, DjangoObjectType):
    class Meta:
        model = ArtistFollow
        interfaces = [graphene.relay.Node, ]

