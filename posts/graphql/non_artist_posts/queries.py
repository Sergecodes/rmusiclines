import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from core.mixins import PKMixin
from posts.models.non_artist_posts.models import (
    NonArtistPost, NonArtistPostComment
)


class NonArtistPostType(DjangoObjectType):
    class Meta:
        model = NonArtistPost


# Graphene will automatically map the NonArtistPost model's fields onto the NonArtistPostNode.
# This is configured in the NonArtistPostNode's Meta class (as you can see below)
class NonArtistPostNode(PKMixin, DjangoObjectType):
    class Meta:
        model = NonArtistPost
        filter_fields = {
            'body': ['exact', 'icontains', 'istartswith'],
            'created_on': ['year__lt', 'year__gt'],
            'is_private': ['exact'],
            'num_ancestor_comments': ['lt', 'gt'],
            'num_stars': ['lt', 'gt'],
        }
        interfaces = [graphene.relay.Node, ]


class NonArtistPostQuery(graphene.ObjectType):
    non_artist_post = graphene.relay.Node.Field(NonArtistPostNode)
    all_non_artist_posts = DjangoFilterConnectionField(NonArtistPostNode)

    # all_non_artist_posts = graphene.List(NonArtistPostNode)
    # non_artist_post_by_uuid = graphene.Field(
    #     NonArtistPostNode, 
    #     uuid=graphene.String(required=True)
    # )

    # def resolve_all_non_artist_posts(root, info):
    #     return NonArtistPost.objects.all()

    # def resolve_non_artist_post_by_uuid(root, info, uuid):
    #     try:
    #         return NonArtistPost.objects.get(uuid=uuid)
    #     except NonArtistPost.DoesNotExist:
    #         return None


'''
class NonArtistPostCommentType(DjangoObjectType):
    can_be_edited = graphene.Boolean(source='can_be_edited')

    class Meta:
        model = NonArtistPostComment
        fields = '__all__'


class NonArtistPostCommentQuery(graphene.ObjectType):
    all_non_artist_post_comments = graphene.List(NonArtistPostCommentType)
    non_artist_post_comment_by_uuid = graphene.Field(
        NonArtistPostCommentType, 
        uuid=graphene.String(required=True)
    )

    def resolve_all_non_artist_post_comments(root, info):
        return NonArtistPostComment.objects.all()
        # return NonArtistPostComment.objects.select_related(
        #     'poster', 'parent'
        # ).all()

    def resolve_non_artist_post_comment_by_uuid(root, info, uuid):
        try:
            return NonArtistPostComment.objects.get(uuid=uuid)
        except NonArtistPostComment.DoesNotExist:
            return None
'''

