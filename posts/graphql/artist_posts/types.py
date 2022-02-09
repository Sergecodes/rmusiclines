import graphene
from graphene_django import DjangoObjectType

from core.mixins import PKMixin
from posts.models.artist_posts.models import (
    ArtistPost, ArtistPostBookmark, ArtistPostComment, ArtistPostDownload, 
    ArtistPostRating, ArtistPostCommentLike, 
)
from ..common.types import CommentFilter, PostFilter


class ArtistPostFilter(PostFilter):
    class Meta(PostFilter.Meta):
        model = ArtistPost


class ArtistPostCommentFilter(CommentFilter):
    class Meta(CommentFilter.Meta):
        model = ArtistPostComment


class ArtistPostNode(PKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPost
        filterset_class = ArtistPostFilter
        interfaces = [graphene.relay.Node, ]


class ArtistPostCommentNode(PKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPostComment
        filterset_class = ArtistPostCommentFilter
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




