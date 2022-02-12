import graphene
import graphene_django_optimizer as gql_optimizer
from graphene_django.filter import DjangoFilterConnectionField

from accounts.models.artists.models import Artist
from core.utils import get_int_id_or_none
from .types import ArtistNode


class ArtistQuery(graphene.ObjectType):
    # This permits accessing an artist via their global ID
    # artist = relay.Node.Field(ArtistNode)

    artist = graphene.Field(
        ArtistNode,
        id=graphene.ID(),
        slug=graphene.String()
    )
    all_artists = DjangoFilterConnectionField(ArtistNode)

    def resolve_artist(root, info, id=None, slug=None):
        """Get artist using either id or slug. If both are passed, id is prioritized."""
        id = get_int_id_or_none(id)

        if id:
            # Use filter so that we can use methods such as select_related, only, ...
            # thus making gql_optimizer work properly
            return gql_optimizer.query(Artist.objects.filter(id=id), info).get()
        elif slug:
            return gql_optimizer.query(Artist.objects.filter(slug=slug), info).get()
        else:
            # If neither id nor slug was passed, return None
            return None

    def resolve_all_artists(root, info):
        return gql_optimizer.query(Artist.objects.all(), info)


