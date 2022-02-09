import graphene
import graphene_django_optimizer as gql_optimizer
from django.utils.translation import gettext_lazy as _
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField

from accounts.models.artists.models import Artist
from .types import ArtistNode



class ArtistQuery(graphene.ObjectType):
    artist = relay.Node.Field(ArtistNode)

    all_artists = DjangoFilterConnectionField(ArtistNode)
    artist_by_slug = graphene.Field(
        ArtistNode, 
        slug=graphene.String(required=True)
    )

    def resolve_all_artists(root, info):
        return gql_optimizer.query(Artist.objects.all(), info)

    def resolve_artist_by_slug(root, info, slug):
        try:
            # Use filter so that we can use methods such as select_related, only, ...
            return gql_optimizer.query(Artist.objects.filter(slug=slug), info).get()
        except Artist.DoesNotExist:
            return Artist.objects.none()

