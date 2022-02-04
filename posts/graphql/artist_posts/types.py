import graphene
from graphene_django import DjangoObjectType

from core.utils import PKMixin
from posts.models.artist_posts.models import (
    ArtistPost, ArtistPostComment,

)


class ArtistPostNode(PKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPost
        filter_fields = ['body']
        filter_fields = {
            'body': ['exact', 'icontains', 'istartswith'],
            'created_on': ['year__lt', 'year__gt'],
            'is_private': ['exact'],
            'num_parent_comments': ['lt', 'gt'],
            'num_stars': ['lt', 'gt'],
        }
        interfaces = [graphene.relay.Node, ]


class ArtistPostCommentNode(PKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPostComment
        interfaces = [graphene.relay.Node, ]




