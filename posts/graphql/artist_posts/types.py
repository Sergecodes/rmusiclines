import graphene
from graphene_django import DjangoObjectType

from core.mixins import GraphenePKMixin, GraphenePhotoMixin
from posts.models.artist_posts.models import (
    ArtistPost, ArtistPostBookmark, ArtistPostComment, ArtistPostDownload, 
    ArtistPostRating, ArtistPostCommentLike, ArtistPostPhoto, ArtistPostVideo,
    ArtistParentPost, ArtistPostRepost
)
from ..common.types import CommentFilter, PostFilter


class ArtistPostFilter(PostFilter):
    class Meta(PostFilter.Meta):
        model = ArtistPost


class ArtistPostCommentFilter(CommentFilter):
    class Meta(CommentFilter.Meta):
        model = ArtistPostComment


class ArtistPostNode(GraphenePKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPost
        filterset_class = ArtistPostFilter
        interfaces = [graphene.relay.Node, ]


class ArtistPostRepostNode(GraphenePKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPostRepost
        filterset_class = ArtistPostFilter
        interfaces = [graphene.relay.Node, ]


class ArtistParentPostNode(GraphenePKMixin, DjangoObjectType):
    class Meta:
        model = ArtistParentPost
        filterset_class = ArtistPostFilter
        interfaces = [graphene.relay.Node, ]


class ArtistPostCommentNode(GraphenePKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPostComment
        filterset_class = ArtistPostCommentFilter
        interfaces = [graphene.relay.Node, ]


class ArtistPostPhotoNode(GraphenePKMixin, GraphenePhotoMixin, DjangoObjectType):
    class Meta:
        model = ArtistPostPhoto
        interfaces = [graphene.relay.Node, ]


class ArtistPostVideoNode(GraphenePKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPostVideo
        interfaces = [graphene.relay.Node, ]


class ArtistPostDownloadNode(GraphenePKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPostDownload
        interfaces = [graphene.relay.Node, ]


class ArtistPostRatingNode(GraphenePKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPostRating
        interfaces = [graphene.relay.Node, ]


class ArtistPostBookmarkNode(GraphenePKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPostBookmark
        interfaces = [graphene.relay.Node, ]


class ArtistPostCommentLikeNode(GraphenePKMixin, DjangoObjectType):
    class Meta:
        model = ArtistPostCommentLike
        interfaces = [graphene.relay.Node, ]




