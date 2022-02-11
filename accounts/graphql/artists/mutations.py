from django.utils.translation import gettext_lazy as _
from graphene import relay
from graphene_django_cud.mutations import (
    DjangoCreateMutation, DjangoPatchMutation,
    DjangoDeleteMutation, DjangoFilterUpdateMutation
)
from graphene_django_cud.util import disambiguate_id
from graphql import GraphQLError
from graphql_auth.bases import Output
from graphql_auth.decorators import login_required

from accounts.mixins import ArtistCUMutationMixin
from accounts.models.artists.models import Artist
# Though it seems like these types aren't used, however, we need to import them
# cause it's implicitly used by graphene when registering mutations
from .types import *


class CreateArtist(Output, DjangoCreateMutation):
    class Meta(ArtistCUMutationMixin.Meta):
        optional_fields = ('slug', 'followers', )
        permissions = ('accounts.add_artist', )
    
    @classmethod
    def after_mutate(cls, root, info, input, obj: Artist, return_data):
        # Set artist's tags
        if tags := input.get('artist_tags'):
            obj.tags.set(tags)

        return super().after_mutate(root, info, input, obj, return_data)

    @classmethod
    def check_permissions(cls, root, info, input):
        ## Though our permissions attribute above would also work, we use this method 
        # since we are able to customize the error message and even use a custom code 
        # "not_permitted"
        
        # Only staff can create artist
        if info.context.user.is_staff:
            # Not raising an Exception means the calling user 
            # has permission to access the mutation
            return 
        else:
            raise GraphQLError(
                _("Only staff can create artist"),
                extensions={'code': "not_permitted"}
            )


class PatchArtist(Output, DjangoPatchMutation):
    class Meta(ArtistCUMutationMixin.Meta):
        permissions = ['accounts.change_artist']

    @classmethod
    def after_mutate(cls, root, info, id, input, obj: Artist, return_data):
        # Update artist's tags
        if tags := input.get('artist_tags'):
            obj.tags.set(tags)

        return super().after_mutate(root, info, id, input, obj, return_data)


class DeleteArtist(Output, DjangoDeleteMutation):
    class Meta:
        model = Artist    
        permissions = ['accounts.delete_artist']  


class FilterUpdateArtist(Output, DjangoFilterUpdateMutation):
    class Meta:
        model = Artist
        permissions = ['accounts.change_artist']  
        exclude_fields = ['tags', ]
        filter_fields = (
            'name',
            'country__code',
        ) 


class FollowArtist(Output, relay.ClientIDMutation):
    class Input:
        artist_id = graphene.ID(required=True)

    artist_follow = graphene.Field(ArtistFollowNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, artist_id):
        user = info.context.user
        follow_obj = user.follow_artist(int(disambiguate_id(artist_id)))

        return cls(artist_follow=follow_obj)


class UnfollowArtist(Output, relay.ClientIDMutation):
    class Input:
        artist_id = graphene.ID(required=True)

    follow_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, artist_id):
        user = info.context.user
        deleted_obj_id = user.unfollow_artist(int(disambiguate_id(artist_id)))

        return cls(follow_id=deleted_obj_id)


