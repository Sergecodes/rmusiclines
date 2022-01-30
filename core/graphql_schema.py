import graphene
from graphene_django.debug import DjangoDebug
from graphql_auth.schema import UserQuery, MeQuery

from accounts.graphql_schema.artists import (
    CreateArtistMutation, PatchArtistMutation, ArtistQuery,
    DeleteArtistMutation, FilterUpdateArtistMutation,
)
from accounts.graphql_schema.users import (
    AuthRelayMutation, PatchUserMutation, 
    ChangeUsernameMutation, 
)
from posts.graphql_schema.non_artist_posts import (
    NonArtistPostQuery, 
)


# All Query objects will be inserted here
class Query(UserQuery, MeQuery, NonArtistPostQuery, ArtistQuery, graphene.ObjectType):
    pass


# All Mutation objects will be inserted here
class Mutation(AuthRelayMutation, graphene.ObjectType):
    debug = graphene.Field(DjangoDebug, name='__debug')

    ## Extra user mutations
    patch_user = PatchUserMutation.Field()
    change_username = ChangeUsernameMutation.Field()

    ## Artist mutations
    create_artist = CreateArtistMutation.Field()
    patch_artist = PatchArtistMutation.Field()
    delete_artist = DeleteArtistMutation.Field()
    filter_update_artist = FilterUpdateArtistMutation.Field()



schema = graphene.Schema(
    query=Query, 
    mutation=Mutation, 
    # types=[ArtistTagType]
)

