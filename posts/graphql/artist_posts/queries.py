import graphene
import graphene_django_optimizer as gql_optimizer
from graphene.types.generic import GenericScalar
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django_cud.util import disambiguate_id
from graphql_auth.decorators import login_required

from accounts.models.artists.models import Artist
from core.utils import get_int_id_or_none
from posts.models.artist_posts.models import ArtistPost, ArtistPostComment
from .types import ArtistPostNode, ArtistPostCommentNode


class ArtistPostQuery(graphene.ObjectType):
    # With this relay Node field, we can only query by global graphene ID.
    # artist_post = relay.Node.Field(ArtistPostNode)

    artist_post = graphene.Field(
        ArtistPostNode,
        id=graphene.ID(),
        uuid=graphene.String()
    )
    all_artist_posts = DjangoFilterConnectionField(ArtistPostNode)
    my_artist_posts = DjangoFilterConnectionField(ArtistPostNode)
    artist_artist_posts = DjangoFilterConnectionField(
        ArtistPostNode,
        artist_id=graphene.ID(),
        artist_slug=graphene.String()
    )
    artist_post_ratings = graphene.Field(
        GenericScalar,
        id=graphene.ID(required=True)
    )

    def resolve_artist_post(root, info, id=None, uuid=None):
        """Get artist post using either id or uuid. If both are passed, id is prioritized.""" 
        id = get_int_id_or_none(id)

        if id:
            return gql_optimizer.query(ArtistPost.objects.filter(id=id), info).get()
        elif uuid:
            return gql_optimizer.query(ArtistPost.objects.filter(uuid=uuid), info).get()
        else:
            # If neither id nor uuid was passed, return None
            return None

    def resolve_all_artist_posts(root, info):
        return gql_optimizer.query(ArtistPost.objects.all(), info)

    # This needs to be a classmethod due to this login_required decorator
    @classmethod
    @login_required
    def resolve_my_artist_posts(cls, root, info):
        return gql_optimizer.query(info.context.user.artist_posts.all(), info)

    def resolve_artist_artist_posts(root, info, artist_id=None, artist_slug=None):
        artist_id = get_int_id_or_none(artist_id)

        if artist_id:
            artist = Artist.objects.get(id=artist_id)
        elif artist_slug:
            artist = Artist.objects.get(slug=artist_slug)
        else:
            # If neither id nor slug was passed, return None
            return None

        return gql_optimizer.query(artist.posts.all(), info)

    def resolve_artist_post_ratings(root, info, id):
        post = ArtistPost.objects.get(id=int(disambiguate_id(id)))
        return post.get_ratings()


class ArtistPostCommentQuery(graphene.ObjectType):
    artist_post_comment = graphene.Field(
        ArtistPostCommentNode,
        id=graphene.ID(),
        uuid=graphene.String()
    )
    artist_post_ancestor_comments = DjangoFilterConnectionField(
        ArtistPostCommentNode,
        post_id=graphene.ID(),
        post_uuid=graphene.String()
    )

    def resolve_artist_post_comment(root, info, id=None, uuid=None):
        id = get_int_id_or_none(id)

        if id:
            return gql_optimizer.query(ArtistPostComment.objects.filter(id=id), info).get()
        elif uuid:
            return gql_optimizer.query(ArtistPostComment.objects.filter(uuid=uuid), info).get()
        else:
            # If neither id nor uuid was passed, return None
            return None

    def resolve_artist_post_ancestor_comments(root, info, post_id=None, post_uuid=None):
        post_id = get_int_id_or_none(post_id)

        if post_id:
            post = ArtistPost.objects.get(id=post_id)
        elif post_uuid:
            post = ArtistPost.objects.get(uuid=post_uuid)
        else:
            # If neither id nor uuid was passed, return None
            return None

        return gql_optimizer.query(post.ancestor_comments.all(), info)


