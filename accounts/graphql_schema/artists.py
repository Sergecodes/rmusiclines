import graphene
from django.contrib.auth import get_user
from graphene_django import DjangoObjectType
from graphene_django_cud.mutations import DjangoCreateMutation

from accounts.models.artists.models import Artist, ArtistTag
from core.utils import GrapheneRenderTaggitTags


## Type
class ArtistTagType(DjangoObjectType):
    class Meta:
        model = ArtistTag
        exclude_fields = ['slug']


class ArtistType(GrapheneRenderTaggitTags, DjangoObjectType):
    class Meta:
        model = Artist
        fields = '__all__'


class ArtistNode(GrapheneRenderTaggitTags, DjangoObjectType):
    class Meta:
        model = Artist
        interfaces = [graphene.relay.Node]


## Query
class ArtistQuery(graphene.ObjectType):
    all_artists = graphene.List(ArtistType)
    artist_by_name = graphene.Field(
        ArtistType, 
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
# Create mutations
class CreateArtistMutation(DjangoCreateMutation):
    @classmethod
    def before_mutate(cls, root, info, *args, **kwargs):
        print("in before mutate mehtod")
        print(root)
        print(info.context)
        print(info.context.user.is_authenticated)
        print(kwargs)
        print(get_user(info.context))
        return super().before_mutate(root, info, kwargs.get('input'))

    class Arguments:
        tags = graphene.List(ArtistTagType, required=False)

    class Meta:
        model = Artist
        exclude_fields = ('tags', )
        optional_fields = ('slug', 'followers', )
        login_required = True
        


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

