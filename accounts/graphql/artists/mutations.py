import graphene
from django.utils.translation import gettext_lazy as _
from graphene_django_cud.mutations import (
    DjangoCreateMutation, DjangoPatchMutation,
    DjangoDeleteMutation, DjangoFilterUpdateMutation
)
from graphql import GraphQLError

from accounts.models.artists.models import Artist
# Though it seems like this type isn't used, however, we need to import it
# cause it's implicitly used by graphene when registering mutations
from .types import ArtistNode


class ArtistCUMutationMixin:
    """Artist Create-Update mutation mixin"""

    class Meta:
        model = Artist
        # Exclude the `tags` field coz graphql complaints that it doesn't
        # know how to convert(serialize) it 
        exclude_fields = ('tags', )
        # Ensure to use a name other than 'tags' else the tags will be 
        # sent to the corresponding model object as a list and will raise errors
        # when trying to save the object.
        custom_fields = {
            "artist_tags": graphene.List(graphene.String)
        }


class CreateArtistMutation(DjangoCreateMutation):
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
                extensions={
                    'code': "not_permitted"
                }
            )


class PatchArtistMutation(DjangoPatchMutation):
    class Meta(ArtistCUMutationMixin.Meta):
        permissions = ['accounts.change_artist']

    @classmethod
    def after_mutate(cls, root, info, id, input, obj: Artist, return_data):
        # Update artist's tags
        if tags := input.get('artist_tags'):
            obj.tags.set(tags)

        return super().after_mutate(root, info, id, input, obj, return_data)


class DeleteArtistMutation(DjangoDeleteMutation):
    class Meta:
        model = Artist    
        permissions = ['accounts.delete_artist']  


class FilterUpdateArtistMutation(DjangoFilterUpdateMutation):
    class Meta:
        model = Artist
        permissions = ['accounts.change_artist']  
        exclude_fields = ['tags', ]
        filter_fields = (
            'name',
            'country__code',
        ) 


