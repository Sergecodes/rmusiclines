import graphene
import graphene_django_optimizer as gql_optimizer
from graphene import relay
from graphene.types.generic import GenericScalar
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django_cud.util import disambiguate_id
from graphql_auth.decorators import login_required

from accounts.models.artists.models import Artist
from posts.models.artist_posts.models import ArtistPost, ArtistPostComment
from .types import ArtistPostNode, ArtistPostCommentNode


class ArtistPostQuery(graphene.ObjectType):
    artist_post = relay.Node.Field(ArtistPostNode)

    get_artist_post = graphene.Field(
        ArtistPostNode,
        pk=graphene.Int(),
        uuid=graphene.String()
    )
    all_artist_posts = DjangoFilterConnectionField(ArtistPostNode)
    my_artist_posts = DjangoFilterConnectionField(ArtistPostNode)
    artist_posts_by_artist_id = DjangoFilterConnectionField(
        ArtistPostNode,
        artist_id=graphene.ID(required=True)
    )
    artist_post_ratings = graphene.Field(
        GenericScalar,
        id=graphene.ID(required=True)
    )

    def resolve_get_artist_post(root, info, pk=None, uuid=None):
        """Get artist post using either pk or uuid. If both are passed, pk is prioritized."""  
        if pk:
            return gql_optimizer.query(ArtistPost.objects.filter(pk=pk), info).get()
        elif uuid:
            return gql_optimizer.query(ArtistPost.objects.filter(uuid=uuid), info).get()
        else:
            # If neither pk nor uuid was passed, return None
            return None

    def resolve_all_artist_posts(root, info):
        return gql_optimizer.query(ArtistPost.objects.all(), info)

    # This needs to be a classmethod due to this login_required decorator
    @classmethod
    @login_required
    def resolve_my_artist_posts(cls, root, info):
        return gql_optimizer.query(info.context.user.artist_posts.all(), info)

    def resolve_artist_posts_by_artist_id(root, info, artist_id):
        artist = Artist.objects.get(id=int(disambiguate_id(artist_id)))
        return gql_optimizer.query(artist.posts.all(), info)

    def resolve_artist_post_ratings(root, info, id):
        post = ArtistPost.objects.get(id=int(disambiguate_id(id)))
        return post.get_ratings()


class ArtistPostCommentQuery(graphene.ObjectType):
    artist_post_comment = relay.Node.Field(ArtistPostCommentNode)

    get_artist_post_comment = graphene.Field(
        ArtistPostCommentNode,
        pk=graphene.Int(),
        uuid=graphene.String()
    )
    ancestor_comments_by_artist_post_id = DjangoFilterConnectionField(
        ArtistPostCommentNode,
        post_id=graphene.ID(required=True)
    )

    def resolve_get_artist_post_comment(root, info, pk=None, uuid=None):
        if pk:
            return gql_optimizer.query(ArtistPostComment.objects.filter(pk=pk), info).get()
        elif uuid:
            return gql_optimizer.query(ArtistPostComment.objects.filter(uuid=uuid), info).get()
        else:
            # If neither pk nor uuid was passed, return None
            return None
        
    def resolve_ancestor_comments_by_artist_post_id(root, info, post_id):
        post = ArtistPost.objects.get(id=int(disambiguate_id(post_id)))
        return gql_optimizer.query(post.ancestor_comments.all(), info)


