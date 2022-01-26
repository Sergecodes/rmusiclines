import graphene
from graphene_django import DjangoObjectType
from graphene_django_cud.mutations import DjangoCreateMutation

from accounts.models.artists.models import Artist, ArtistTag
from core.utils import PKMixin


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


class ArtistNode(PKMixin, DjangoObjectType):
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
    artist_tags = graphene.List(graphene.String, required=False)

    @classmethod
    def after_mutate(cls, root, info, input, obj, return_data):
        # Set tags of artist
        if tags := input.get('artist_tags'):
            obj.tags.add(*tags)

        return super().after_mutate(root, info, input, obj, return_data)

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
            "artist_tags": graphene.List(graphene.String, required=False)
        }
        



# class ArtistCreateMutation(
#     mixins.LoginRequiredMutationMixin, 
#     mutations.CreateModelMutation
# ):
#     class Meta:
#         serializer_class = ArtistSerializer


# class ArtistBulkCreateMutation(
#     mixins.LoginRequiredMutationMixin, 
#     mutations.CreateBulkModelMutation
# ):
#     class Meta:
#         serializer_class = ArtistSerializer
        

# # Update mutations
# class ArtistUpdateMutation(
#     mixins.LoginRequiredMutationMixin, 
#     mutations.UpdateModelMutation
# ):

#     class Meta:
#         serializer_class = ArtistSerializer


# class ArtistBulkUpdateMutation(
#     mixins.LoginRequiredMutationMixin, 
#     mutations.UpdateBulkModelMutation
# ):
#     class Arguments:
#         pass

#     class Meta:
#         model = Artist


# # Delete mutations
# class ArtistDeleteMutation(
#     mixins.LoginRequiredMutationMixin,
#     mutations.DeleteModelMutation
# ):
#     class Meta:
#         model = Artist


# class ArtistBulkDeleteMutation(
#     mixins.LoginRequiredMutationMixin,
#     mutations.DeleteBulkModelMutation
# ):
#     class Meta:
#         model = Artist



# @convert_django_field.register(TaggableManager)
# def convert_field_to_string(field, registry=None):
#     print(field)
#     print("to string??")
#     return graphene.String(description=field.help_text, required=not field.null)

