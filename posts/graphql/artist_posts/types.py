import graphene
from graphene_django import DjangoObjectType

from core.utils import PKMixin
from posts.models.artist_posts.models import (
    ArtistPost, ArtistPostBookmark, ArtistPostComment, ArtistPostDownload, 
    ArtistPostRating, ArtistPostCommentLike, 

)


class ArtistPostNode(PKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPost
        filter_fields = ['body']
        filter_fields = {
            'body': ['exact', 'icontains', 'istartswith'],
            'created_on': ['year__lt', 'year__gt'],
            'is_private': ['exact'],
            'num_ancestor_comments': ['lt', 'gt'],
            'num_stars': ['lt', 'gt'],
        }
        interfaces = [graphene.relay.Node, ]


class ArtistPostCommentNode(PKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPostComment
        interfaces = [graphene.relay.Node, ]


class ArtistPostDownloadNode(PKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPostDownload
        interfaces = [graphene.relay.Node, ]


class ArtistPostRatingNode(PKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPostRating
        interfaces = [graphene.relay.Node, ]


class ArtistPostBookmarkNode(PKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPostBookmark
        interfaces = [graphene.relay.Node, ]


class ArtistPostCommentLikeNode(PKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPostCommentLike
        interfaces = [graphene.relay.Node, ]




