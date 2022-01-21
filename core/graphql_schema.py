import graphene
from graphql_auth.schema import UserQuery, MeQuery
from graphene_django.debug import DjangoDebug

from accounts.graphql_schema.artists import (
    CreateArtistMutation, ArtistQuery,
)
from accounts.graphql_schema.users import (
    AuthRelayMutation
)
from posts.graphql_schema.non_artist_posts import (
    NonArtistPostQuery, 
)


# This class will inherit from multiple Queries from the different apps
class Query(UserQuery, MeQuery, NonArtistPostQuery, ArtistQuery, graphene.ObjectType):
    pass


# All Mutation objects will be placed here
class Mutation(AuthRelayMutation, graphene.ObjectType):
    # Artist mutations
    debug = graphene.Field(DjangoDebug, name='__debug')
    artist_create = CreateArtistMutation.Field()
    # artist_delete = ArtistSerializerMutation.DeleteField()
    # artist_update = ArtistSerializerMutation.UpdateField()
    # artist_create = ArtistCreateMutation.Field()
    # # artist_update = ArtistUpdateMutation.Field()
    # artist_delete = ArtistDeleteMutation.Field()
    # artist_bulk_create = ArtistBulkCreateMutation.Field()
    # artist_bulk_update = ArtistBulkUpdateMutation.Field()
    # artist_bulk_delete = ArtistBulkDeleteMutation.Field()
   

schema = graphene.Schema(query=Query, mutation=Mutation)

