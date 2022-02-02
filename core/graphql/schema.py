import graphene
from graphene_django.debug import DjangoDebug
from graphql_auth.schema import UserQuery, MeQuery

from accounts.graphql.artists.mutations import (
    CreateArtistMutation, PatchArtistMutation,
    DeleteArtistMutation, FilterUpdateArtistMutation,
)
from accounts.graphql.artists.queries import ArtistQuery
from accounts.graphql.users.mutations import (
    AuthRelayMutation, PatchUserMutation, 
    ChangeUsernameMutation, ChangeEmailMutation,
    VerifyNewEmailMutation
)
from posts.graphql.non_artist_posts.queries import (
    NonArtistPostQuery, 
)
from .mutations import (
    DeleteImageMutation, SingleImageUploadMutation, 
    MultipleImageUploadMutation
)


# All Queries will be inherited here
class Query(UserQuery, MeQuery, NonArtistPostQuery, ArtistQuery, graphene.ObjectType):
    pass


# All Mutations will be inherited here
class Mutation(AuthRelayMutation, graphene.ObjectType):
    debug = graphene.Field(DjangoDebug, name='__debug')

    ## Core mutations
    single_image_upload = SingleImageUploadMutation.Field()
    multiple_image_upload = MultipleImageUploadMutation.Field()
    delete_image = DeleteImageMutation.Field()

    ## Extra user mutations
    patch_user = PatchUserMutation.Field()
    change_username = ChangeUsernameMutation.Field()
    change_email = ChangeEmailMutation.Field()
    verify_new_email = VerifyNewEmailMutation.Field()

    ## Artist mutations
    create_artist = CreateArtistMutation.Field()
    patch_artist = PatchArtistMutation.Field()
    delete_artist = DeleteArtistMutation.Field()
    filter_update_artist = FilterUpdateArtistMutation.Field()



schema = graphene.Schema(
    query=Query, 
    mutation=Mutation, 
    # types=[]
)


