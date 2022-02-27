import base64
import graphene
from actstream.actions import follow, unfollow
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from graphene import relay
from graphene_django_cud.mutations import (
    DjangoCreateMutation, DjangoPatchMutation,
    DjangoDeleteMutation, DjangoFilterUpdateMutation,
    DjangoBatchDeleteMutation
)
from graphene_django_cud.util import disambiguate_id
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from graphql_auth.bases import Output
from graphql_auth.decorators import login_required
from io import BytesIO
from PIL import Image

from accounts.constants import ARTISTS_PHOTOS_UPLOAD_DIR
from accounts.mixins import ArtistCUMutationMixin
from accounts.models.artists.models import Artist, ArtistPhoto
from accounts.utils import get_artist_photos_upload_path
from accounts.validators import validate_artist_photo
from core.constants import FILE_STORAGE_CLASS
from core.utils import get_image_file_thumbnail_extension_and_type
from .types import ArtistFollowNode

STORAGE = FILE_STORAGE_CLASS()
THUMBNAIL_ALIASES = settings.THUMBNAIL_ALIASES


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
        user, artist_id = info.context.user, int(disambiguate_id(artist_id))
        artist = Artist.objects.get(id=artist_id)
        follow_obj = user.follow_artist(artist)

        # Add action
        follow(user, artist)

        return cls(artist_follow=follow_obj)


class UnfollowArtist(Output, relay.ClientIDMutation):
    class Input:
        artist_id = graphene.ID(required=True)

    follow_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, artist_id):
        user, artist_id = info.context.user, int(disambiguate_id(artist_id))
        artist = Artist.objects.get(id=artist_id)
        deleted_obj_id = user.unfollow_artist(artist)

        # Remove action
        unfollow(user, artist)

        return cls(follow_id=deleted_obj_id)


class UploadArtistPhotos(Output, graphene.ClientIDMutation):
    class Input:
        artist_id = graphene.ID(required=True)
        files = graphene.List(Upload, required=True)
    
    filenames = graphene.List(graphene.String)
    base64_strs = graphene.List(graphene.String)
    mimetypes = graphene.List(graphene.String)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, artist_id, files: list):
        # Only staff is permitted to upload artist photo
        user = info.context.user
        if not user.is_staff:
            raise GraphQLError(
                _("You are not permitted to upload artist photos"),
                extensions={'code': 'invalid'}
            ) 

        # Validate files
        for file in files:
            validate_artist_photo(file)

        artist = Artist.objects.get(id=int(disambiguate_id(artist_id)))
        artist_photos = []

        # Get thumbnails of files and saved to cache
        base64_strs, filenames, mimetypes = [], [], []
        for file in files:
            # Get file extension and type to use with PIL
            file_extension, ftype = get_image_file_thumbnail_extension_and_type(file)

            image = Image.open(file)
            # image = image.convert('RGB')
            image.thumbnail(THUMBNAIL_ALIASES['']['artist_photo']['size'], Image.ANTIALIAS)
            thumb_file = BytesIO()
            image.save(thumb_file, format=ftype)
            
            use_filename = file.name
            mimetype = file.content_type
            file_bytes = thumb_file.getvalue()
            img_file = ContentFile(file_bytes)
            save_dir = get_artist_photos_upload_path(
                artist.slug,
                ARTISTS_PHOTOS_UPLOAD_DIR,
                use_filename
            )
            saved_filename = STORAGE.save(save_dir, img_file)
            artist_photos.append(
                ArtistPhoto(artist=artist, photo=saved_filename, uploaded_by=user)
            )

            # Update return info
            base64_strs.append(base64.b64encode(file_bytes).decode('utf-8'))
            filenames.append(use_filename)
            mimetypes.append(mimetype)
            thumb_file.close()

        # Save photos to artist
        ArtistPhoto.objects.bulk_create(artist_photos)

        return cls(
            filenames=filenames,
            base64_strs=base64_strs,
            mimetypes=mimetypes
        )


class BatchDeleteArtistPhoto(Output, DjangoBatchDeleteMutation):
    class Meta:
        model = ArtistPhoto
        permissions = ('accounts.delete_artistphoto', )

    @classmethod
    @login_required
    def mutate(cls, root, info, ids):
        return super().mutate(root, info, ids)



# class DeleteArtistPhotos(Output, graphene.ClientIDMutation):

#     class Input:
#         artist_id = graphene.ID(required=True)
#         filenames = graphene.List(graphene.String, required=True)

#     deleted_filenames = graphene.List(graphene.String)

#     @classmethod
#     @login_required
#     def mutate_and_get_payload(cls, root, info, artist_id, filenames: list):
#         # Only staff is permitted to upload artist photo
#         user = info.context.user
#         if not user.is_staff:
#             raise GraphQLError(
#                 _("You are not permitted to delete artist photos"),
#                 extensions={'code': 'invalid'}
#             ) 

#         # Get and delete files with passed filenames
#         # Get actual filenames (names of the form artists/artist_<slug>/filename) since these
#         # will be used to filter and delete files as we can't use the passef filename
#         artist = Artist.objects.get(id=int(disambiguate_id(artist_id)))

#         actual_filenames = []
#         for filename in filenames:
#             actual_filenames.append(
#                 get_artist_photos_upload_path(
#                     artist.slug,
#                     ARTISTS_PHOTOS_UPLOAD_DIR,
#                     filename
#                 )
#             )
            
#         photos = ArtistPhoto.objects.filter(photo__in=actual_filenames)

#         # os.path.split is used to get the filename and not the path
#         photo_names = [os.path.split(photo.photo)[-1] for photo in photos]
#         photos._raw_delete(photos.db)

#         return cls(deleted_filenames=photo_names)


