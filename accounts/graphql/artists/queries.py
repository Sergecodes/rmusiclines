import graphene
from django.utils.translation import gettext_lazy as _

from accounts.models.artists.models import Artist
from .types import ArtistNode


class ArtistQuery(graphene.ObjectType):
    artists = graphene.List(ArtistNode)
    artist_by_name = graphene.Field(
        ArtistNode, 
        name=graphene.String(required=True)
    )
    # artist_by_tags = graphene.List(graphene.String)

    def resolve_all_artists(root, info):
        return Artist.objects.all()

    def resolve_artist_by_name(root, info, name):
        try:
            return Artist.objects.get(name=name)
        except Artist.DoesNotExist:
            return None

