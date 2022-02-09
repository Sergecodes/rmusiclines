import graphene
import graphene_django_optimizer as gql_optimizer
from graphene import relay
from graphene.types.generic import GenericScalar
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django_cud.util import disambiguate_id
from graphql_auth.decorators import login_required

from accounts.models.artists.models import Artist
# from core.decorators import custom_login_required
from posts.models.artist_posts.models import ArtistPost
from .types import ArtistPostNode, ArtistPostCommentNode


class ArtistPostQuery(graphene.ObjectType):
    artist_post = relay.Node.Field(ArtistPostNode)

    all_artist_posts = DjangoFilterConnectionField(ArtistPostNode)
    my_artist_posts = DjangoFilterConnectionField(ArtistPostNode)
    artist_post_by_uuid = graphene.Field(
        ArtistPostNode, 
        uuid=graphene.String(required=True)
    )
    artist_posts_by_artist_id = DjangoFilterConnectionField(
        ArtistPostNode,
        artist_id=graphene.ID(required=True)
    )
    artist_post_ratings = graphene.Field(
        GenericScalar,
        id=graphene.ID(required=True)
    )
    # artist_post_simple_reposts = DjangoFilterConnectionField(
    #     ArtistPostNode,
    #     id=graphene.ID(required=True)
    # )
    # artist_post_non_simple_reposts = DjangoFilterConnectionField(
    #     ArtistPostNode,
    #     id=graphene.ID(required=True)
    # )

    def resolve_all_artist_posts(root, info):
        return gql_optimizer.query(ArtistPost.objects.all(), info)

    # I think i need to use 'self' due to this decorator
    @login_required
    def resolve_my_artist_posts(self, root, info):
        return gql_optimizer.query(info.context.user.artist_posts.all(), info)

    def resolve_artist_post_by_uuid(root, info, uuid):
        try:
            return gql_optimizer.query(ArtistPost.objects.get(uuid=uuid), info).get()
        except ArtistPost.DoesNotExist:
            # According to graphene_django, if our resolver uses a DjangoObjectType,
            # we should always return a queryset
            return ArtistPost.objects.none()

    def resolve_artist_posts_by_artist_id(root, info, artist_id):
        artist = Artist.objects.get(id=disambiguate_id(artist_id))
        return gql_optimizer.query(artist.posts.all(), info)

    def resolve_artist_post_ratings(root, info, id):
        post = ArtistPost.objects.get(id=disambiguate_id(id))
        return post.get_ratings()

    # def resolve_artist_post_simple_reposts(root, info, id): 
    #     post = ArtistPost.objects.get(id=id)
    #     return gql_optimizer.query(post.simple_reposts.all(), info)

    # def resolve_artist_post_non_simple_reposts(root, info, id): 
    #     post = ArtistPost.objects.get(id=id)
    #     return gql_optimizer.query(post.non_simple_reposts.all(), info)


class ArtistPostCommentQuery(graphene.ObjectType):
    artist_post_comment = relay.Node.Field(ArtistPostCommentNode)

    ancestor_comments_by_artist_post_id = DjangoFilterConnectionField(
        ArtistPostCommentNode,
        post_id=graphene.ID(required=True)
    )

    def resolve_ancestor_comments_by_artist_post_id(root, info, post_id):
        post = ArtistPost.objects.get(id=disambiguate_id(post_id))
        return gql_optimizer.query(post.ancestor_comments.all(), info)


