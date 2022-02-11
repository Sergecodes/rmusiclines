import graphene
import graphene_django_optimizer as gql_optimizer
from django.utils.translation import gettext_lazy as _
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField

from accounts.models.artists.models import Artist
from .types import ArtistNode


class ArtistQuery(graphene.ObjectType):
    # This permits accessing an artist via their global ID
    artist = relay.Node.Field(ArtistNode)

    get_artist = graphene.Field(
        ArtistNode,
        pk=graphene.Int(),
        slug=graphene.String()
    )
    all_artists = DjangoFilterConnectionField(ArtistNode)

    def resolve_get_artist(root, info, pk=None, slug=None):
        """Get artist post using either pk or slug. If both are passed, pk is prioritized."""
        if pk:
            # Use filter so that we can use methods such as select_related, only, ...
            # thus making gql_optimizer work properly
            return gql_optimizer.query(Artist.objects.filter(pk=pk), info).get()
        elif slug:
            return gql_optimizer.query(Artist.objects.filter(slug=slug), info).get()
        else:
            # If neither pk nor slug was passed, return None
            return None

    def resolve_all_artists(root, info):
        return gql_optimizer.query(Artist.objects.all(), info)


