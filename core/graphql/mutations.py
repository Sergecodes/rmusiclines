"""For common / core mutations"""

import base64
import graphene
import os
import uuid
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.files import get_thumbnailer
from easy_thumbnails.templatetags.thumbnail import thumbnail_url
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from io import BytesIO
from PIL import Image

from core.constants import FILE_STORAGE_CLASS, ImageFormEnum as FormForEnum
from core.decorators import verification_and_login_required
from core.graphql.types import ImageFormEnum
from core.forms import ArtistPhotoForm
from posts.constants import (
    MAX_NUM_PHOTOS, ARTIST_POSTS_PHOTOS_UPLOAD_DIR,
    NON_ARTIST_POSTS_PHOTOS_UPLOAD_DIR
)
from posts.validators import validate_post_photo_file

STORAGE = FILE_STORAGE_CLASS()
# Initialise form upload dict
FORM_AND_UPLOAD_DIR = {
    FormForEnum.ARTIST_POST_PHOTO.value: ARTIST_POSTS_PHOTOS_UPLOAD_DIR,
    FormForEnum.NON_ARTIST_POST_PHOTO.value: NON_ARTIST_POSTS_PHOTOS_UPLOAD_DIR,
}
THUMBNAIL_ALIASES = settings.THUMBNAIL_ALIASES


class SingleImageUploadMutation(graphene.Mutation):
    """Upload an image"""

    class Arguments:
        file = Upload(required=True)
        form_for = ImageFormEnum(required=True)

    success = graphene.Boolean(default_value=True)
    filename = graphene.String()
    base64_str = graphene.String()
    mimetype = graphene.String()
     
    # Apparently this should be an instance method not a class method
    @verification_and_login_required
    def mutate(self, info, file: InMemoryUploadedFile, form_for, **kwargs):
        # print(info.context.FILES)
        # form = ArtistPhotoForm({'photo': file})
        # print(form.data)
        # print(form.is_valid())

        if form_for in ['artist_post_photo', 'non_artist_post_photo']:
            try:
                validate_post_photo_file(file)
            except ValidationError as err:
                raise GraphQLError(
                    err.message % (err.params or {}),
                    extensions={'code': err.code}
                )
        else:
            raise GraphQLError(
                _('Invalid `form_for` parameter'),
                extensions={'code': 'invalid'}
            )
        
        cache_key = f'{info.context.user.username}-unposted-photos'
        # Use None so this value stays in the cache indefinitely, till explicitly deleted
        # (or server restarts xD)
        user_photos_list = cache.get_or_set(cache_key, [], None)

        # Validate photos length
        if len(user_photos_list) == MAX_NUM_PHOTOS:
            raise GraphQLError(
                _('Maximum number of photos attained'),
                extensions={'code': 'max_photos_attained'}
            )

        ## Save file to cache
        # Get name without extension
        # valid_filename = STORAGE.get_valid_name(file.name).split('.')[0]

        ## Get thumbnail of file and save to cache
        thumb_name, thumb_extension = os.path.splitext(file.name)
        thumb_extension = thumb_extension.lower()
        file_extension = thumb_extension

        if thumb_extension in ['.jpg', '.jpeg']:
            FTYPE = 'JPEG'
        elif thumb_extension == '.gif':
            FTYPE = 'GIF'
        elif thumb_extension == '.png':
            FTYPE = 'PNG'
        else:
            raise GraphQLError(
                _('Weird, unrecognized file type'),
                extensions={'code': 'invalid_image'}
            )

        # Save thumbnail to in-memory file as StringIO
        image = Image.open(file)
        # image = image.convert('RGB')
        image.thumbnail(THUMBNAIL_ALIASES['']['sm_thumb']['size'], Image.ANTIALIAS)
        thumb_file = BytesIO()
        image.save(thumb_file, format=FTYPE)

        # Use random uuid as filename so as to protect user privacy; and besides we don't
        # really need the file name.
        use_filename = str(uuid.uuid4()) + file_extension
        # thumb_file.seek(0)
        base64_bytes = base64.b64encode(thumb_file.getvalue())
        base64_str = base64_bytes.decode('utf-8')
        mimetype = file.content_type
        # save_dir = FORM_AND_UPLOAD_DIR[form_for]
        # saved_filename = STORAGE.save(save_dir + use_filename, file)

        print(file.size, thumb_file.tell())
        user_photos_list.append({
            'filename': use_filename,
            'base64_str': base64_str,
            'mimetype': mimetype
        })
        cache.set(cache_key, user_photos_list)
        thumb_file.close()

        return SingleImageUploadMutation(
            success=True, 
            base64_str=base64_str,
            filename=use_filename,
            mimetype=mimetype
        )
       
        
class MultipleImageUploadMutation(graphene.Mutation):
    """Upload multiple images at once"""

    class Arguments:
        files = graphene.List(Upload, required=True)
        form_for = ImageFormEnum(required=True)

    success = graphene.Boolean(default_value=True)
    filenames = graphene.List(graphene.String)
    base64_strs = graphene.List(graphene.String)
    mimetypes = graphene.List(graphene.String)
     
    # Apparently this should be an instance method not a class method
    @verification_and_login_required
    def mutate(self, info, files: list[InMemoryUploadedFile], form_for, **kwargs):
        # Validate number of uploaded photos
        if len(files) > MAX_NUM_PHOTOS:
            raise GraphQLError(
                _('Maximum number of photos attained'),
                extensions={'code': 'max_photos_attained'}
            )

        if form_for in ['artist_post_photo', 'non_artist_post_photo']:
            for file in files:
                try:
                    validate_post_photo_file(file)
                except ValidationError as err:
                    raise GraphQLError(
                        err.message % (err.params or {}),
                        extensions={'code': err.code}
                    )
        else:
            raise GraphQLError(
                _('Invalid `form_for` parameter'),
                extensions={'code': 'invalid'}
            )
        
        cache_key = f'{info.context.user.username}-unposted-photos'
        # Use None so this value stays in the cache indefinitely, till explicitly deleted
        # (or server restarts xD)
        user_photos_list = cache.get_or_set(cache_key, [], None)

        # Validate photos length
        if len(files) + len(user_photos_list) > MAX_NUM_PHOTOS:
            raise GraphQLError(
                _('Maximum number of photos attained'),
                extensions={'code': 'max_photos_attained'}
            )

        # Get thumbnails of files and saved to cache
        base64_strs, filenames, mimetypes = [], [], []
        for file in files:
            # Get thumbnail of file
            thumb_name, thumb_extension = os.path.splitext(file.name)
            thumb_extension = thumb_extension.lower()
            file_extension = thumb_extension

            if thumb_extension in ['.jpg', '.jpeg']:
                FTYPE = 'JPEG'
            elif thumb_extension == '.gif':
                FTYPE = 'GIF'
            elif thumb_extension == '.png':
                FTYPE = 'PNG'
            else:
                raise GraphQLError(
                    _('Weird, unrecognized file type'),
                    extensions={'code': 'invalid_image'}
                )

            image = Image.open(file)
            # image = image.convert('RGB')
            image.thumbnail(THUMBNAIL_ALIASES['']['sm_thumb']['size'], Image.ANTIALIAS)
            thumb_file = BytesIO()
            image.save(thumb_file, format=FTYPE)
            
            use_filename = str(uuid.uuid4()) + file_extension
            mimetype = file.content_type
            base64_bytes = base64.b64encode(thumb_file.getvalue())
            base64_str = base64_bytes.decode('utf-8')

            base64_strs.append(base64_str)
            filenames.append(use_filename)
            mimetypes.append(mimetype)
            thumb_file.close()

            user_photos_list.append({
                'filename': use_filename,
                'base64_str': base64_str,
                'mimetype': mimetype
            })
        
        cache.set(cache_key, user_photos_list)

        return MultipleImageUploadMutation(
            success=True, 
            filenames=filenames,
            base64_strs=base64_strs,
            mimetypes=mimetypes
        )
       

class DeleteImageMutation(graphene.Mutation):
    """Delete an uploaded image via its filename"""

    class Arguments:
        filename = graphene.String()
        form_for = ImageFormEnum(required=True)

    success = graphene.Boolean(default_value=True)

    # Apparently this should be an instance method not a class method
    @verification_and_login_required
    def mutate(self, info, filename, form_for, **kwargs):
        if form_for not in ['artist_post_photo', 'non_artist_post_photo']:
            raise GraphQLError(
                _('Invalid `form_for` parameter'),
                extensions={'code': 'invalid'}
            )

        cache_key = f'{info.context.user.username}-unposted-photos'
        # Use None so this value stays in the cache indefinitely, till explicitly deleted
        # (or server restarts xD)
        user_photos_list = cache.get_or_set(cache_key, [], None)

        # Find file name in cache
        for i in range(len(user_photos_list)):
            photo_dict = user_photos_list[i]

            if photo_dict['filename'] == filename:
                del_index = i
                break
        else:
            # If the for loop is not broken(break-ed) - (if the filename is not found)
            # this will be executed.
            # 
            # In other words, this statement will be executed only if the loop completes.
            raise GraphQLError(
                _('No such file found'),
                extensions={'code': 'not_found'}
            )

        del user_photos_list[del_index]
        cache.set(cache_key, user_photos_list)

        return DeleteImageMutation(success=True)


