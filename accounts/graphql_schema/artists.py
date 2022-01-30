import graphene
from django.utils.translation import gettext_lazy as _
from graphene_django import DjangoObjectType
from graphene_django_cud.mutations import (
    DjangoCreateMutation, DjangoPatchMutation,
    DjangoDeleteMutation, DjangoFilterUpdateMutation
)
from graphql import GraphQLError

from accounts.models.artists.models import Artist, ArtistTag
from core.utils import PKMixin, GrapheneRenderTaggitTags


### ARTISTS
class ArtistNode(PKMixin, GrapheneRenderTaggitTags, DjangoObjectType):
    class Meta:
        model = Artist
        interfaces = [graphene.relay.Node, ]


## Queries
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


## Mutations
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



'''
### ARTIST_TAGS
class ArtistNode(PKMixin, GrapheneRenderTaggitTags, DjangoObjectType):
    class Meta:
        model = Artist
        interfaces = [graphene.relay.Node, ]


## Queries
class ArtistQuery(graphene.ObjectType):
    all_artists = graphene.List(ArtistNode)
    artist_by_name = graphene.Field(
        ArtistNode, 
        name=graphene.String(required=True)
    )

    def resolve_all_artists(root, info):
        return Artist.objects.all()

    def resolve_artist_by_name(root, info, name):
        try:
            return Artist.objects.get(name=name)
        except Artist.DoesNotExist:
            return None


## Mutations
class CreateArtistMutation(DjangoCreateMutation):

    class Meta:
        model = Artist
        # Exclude the `tags` field coz graphql complaints that it doesn't
        # know how to convert(serialize) it 
        exclude_fields = ('tags', )
        optional_fields = ('slug', 'followers', )
        # Ensure to use a name other than 'tags' else the tags will be 
        # sent to the corresponding model object as a list and will raise errors
        # when trying to save the object.
        custom_fields = {
            "artist_tags": graphene.List(graphene.String)
        }
        permissions = ('accounts.add_artist', )
        
    
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

    @classmethod
    def after_mutate(cls, root, info, input, obj: Artist, return_data):
        # Set tags of artist
        if tags := input.get('artist_tags'):
            obj.tags.add(*tags)

        return super().after_mutate(root, info, input, obj, return_data)


class PatchArtistMutation(DjangoPatchMutation):
    class Meta:
        model = Artist
        permissions = ['accounts.change_artist']


class DeleteArtistMutation(DjangoDeleteMutation):
    class Meta:
        model = Artist    
        permissions = ['accounts.delete_artist']  


class FilterUpdateArtistMutation(DjangoFilterUpdateMutation):
    class Meta:
        model = Artist
        permissions = ['accounts.change_artist']  
        filter_fields = (
            'name',
            'country__code',
            'tags__name__icontains'
        ) 

'''


'''
## Types
# class ArtistTagType(DjangoObjectType):
#     class Meta:
#         model = ArtistTag
#         exclude_fields = ['slug']


# class ArtistTagNode(PKMixin, DjangoObjectType):
#     class Meta:
#         model = ArtistTag
#         exclude_fields = ['slug']
#         interfaces = [graphene.relay.Node, ]


# class ArtistType(PKMixin, DjangoObjectType):
#     class Meta:
#         model = Artist
#         fields = '__all__'
'''

