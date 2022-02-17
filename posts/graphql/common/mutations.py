"""For common / core mutations"""

import base64
import graphene
import uuid
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import gettext_lazy as _
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from graphql_auth.bases import Output
from graphql_auth.decorators import login_required
from io import BytesIO
from PIL import Image

from core.constants import FILE_STORAGE_CLASS
from core.utils import get_image_file_thumbnail_extension_and_type, get_user_cache_keys
from posts.constants import MAX_NUM_PHOTOS
from posts.graphql.common.types import PostFormFor
from posts.validators import (
    validate_post_photo_file, validate_cache_media,
    validate_post_video_file
)

STORAGE = FILE_STORAGE_CLASS()
THUMBNAIL_ALIASES = settings.THUMBNAIL_ALIASES


class SingleImageUploadMutation(Output, graphene.Mutation):
    """Upload an image"""

    class Arguments:
        file = Upload(required=True)
        form_for = PostFormFor(required=True)

    filename = graphene.String()
    base64_str = graphene.String()
    mimetype = graphene.String()
     
    @classmethod
    @login_required
    def mutate(cls, root, info, file: InMemoryUploadedFile, form_for, **kwargs):
        # print(info.context.FILES)
        # form = ArtistPhotoForm({'photo': file})
        # print(form.data)
        # print(form.is_valid())

        user_cache_keys = get_user_cache_keys(info.context.user.username)
        cache_photos_key, cache_video_key = user_cache_keys['photos'], user_cache_keys['video']

        # Validate cache content
        validate_cache_media(file, cache_photos_key, cache_video_key)

        try:
            validate_post_photo_file(file)
        except ValidationError as err:
            raise GraphQLError(
                err.message % (err.params or {}),
                extensions={'code': err.code}
            )

        # Use None so this value stays in the cache indefinitely, till explicitly deleted
        # (or server restarts xD)
        cache_key = cache_photos_key
        user_photos_list = cache.get_or_set(cache_key, [], None)

        ## Save file to cache
        # Get name without extension
        # valid_filename = STORAGE.get_valid_name(file.name).split('.')[0]

        # Get file extension and type to use with PIL
        file_extension, ftype = get_image_file_thumbnail_extension_and_type(file)

        # Save thumbnail to in-memory file as StringIO
        image = Image.open(file)
        # image = image.convert('RGB')
        image.thumbnail(THUMBNAIL_ALIASES['']['sm_thumb']['size'], Image.ANTIALIAS)
        thumb_file = BytesIO()
        image.save(thumb_file, format=ftype)

        # Use random uuid as filename so as to protect user privacy; and besides we don't
        # really need the file name.
        use_filename = str(uuid.uuid4()) + file_extension
        # thumb_file.seek(0)

        # Will be used with ContentFile to regenerate the file so as to save to
        # model object when posting a post
            # from django.core.files.base import ContentFile
            # img_file = ContentFile(img_io.getvalue())
            # saved_file_name = STORAGE.save(save_dir + valid_name, img_file)

        file_bytes = thumb_file.getvalue()
        base64_bytes = base64.b64encode(file_bytes)
        base64_str = base64_bytes.decode('utf-8')
        mimetype = file.content_type
        # save_dir = FORM_AND_UPLOAD_DIR[form_for]
        # saved_filename = STORAGE.save(save_dir + use_filename, file)

        print(file.size, thumb_file.tell())
        user_photos_list.append({
            'file_bytes': file_bytes,
            'filename': use_filename,
            'mimetype': mimetype
        })
        cache.set(cache_key, user_photos_list)
        thumb_file.close()

        return SingleImageUploadMutation(
            base64_str=base64_str,
            filename=use_filename,
            mimetype=mimetype
        )
       
        
class MultipleImageUploadMutation(Output, graphene.Mutation):
    """Upload multiple images at once"""

    class Arguments:
        files = graphene.List(Upload, required=True)
        form_for = PostFormFor(required=True)

    filenames = graphene.List(graphene.String)
    base64_strs = graphene.List(graphene.String)
    mimetypes = graphene.List(graphene.String)
     
    @classmethod
    @login_required
    def mutate(cls, root, info, files: list[InMemoryUploadedFile], form_for, **kwargs):
        user_cache_keys = get_user_cache_keys(info.context.user.username)
        cache_photos_key, cache_video_key = user_cache_keys['photos'], user_cache_keys['video']

        # Validate cache content and uploaded file
        for file in files:
            validate_cache_media(file, cache_photos_key, cache_video_key)

            try:
                validate_post_photo_file(file)
            except ValidationError as err:
                raise GraphQLError(
                    err.message % (err.params or {}),
                    extensions={'code': err.code}
                )

        # Use None so this value stays in the cache indefinitely, till explicitly deleted
        # (or server restarts xD)
        cache_key = cache_photos_key
        user_photos_list = cache.get_or_set(cache_key, [], None)

        # Validate photos length(if number of photos uploaded plus previous ones will be
        # more than the limit)
        if len(files) + len(user_photos_list) > MAX_NUM_PHOTOS:
            raise GraphQLError(
                _('Maximum number of photos attained'),
                extensions={'code': 'max_photos_attained'}
            )

        # Get thumbnails of files and saved to cache
        base64_strs, filenames, mimetypes = [], [], []
        for file in files:
            # Get file extension and type to use with PIL
            file_extension, ftype = get_image_file_thumbnail_extension_and_type(file)

            image = Image.open(file)
            # image = image.convert('RGB')
            image.thumbnail(THUMBNAIL_ALIASES['']['sm_thumb']['size'], Image.ANTIALIAS)
            thumb_file = BytesIO()
            image.save(thumb_file, format=ftype)
            
            use_filename = str(uuid.uuid4()) + file_extension
            mimetype = file.content_type
            file_bytes = thumb_file.getvalue()
            base64_bytes = base64.b64encode(file_bytes)
            base64_str = base64_bytes.decode('utf-8')

            base64_strs.append(base64_str)
            filenames.append(use_filename)
            mimetypes.append(mimetype)
            thumb_file.close()

            user_photos_list.append({
                'file_bytes': file_bytes,
                'filename': use_filename,
                'mimetype': mimetype
            })
        
        cache.set(cache_key, user_photos_list)

        return MultipleImageUploadMutation(
            filenames=filenames,
            base64_strs=base64_strs,
            mimetypes=mimetypes
        )
       

class DeleteImageMutation(Output, graphene.Mutation):
    """Delete an uploaded image via its filename"""

    class Arguments:
        filename = graphene.String()
        form_for = PostFormFor(required=True)

    @classmethod
    @login_required
    def mutate(cls, root, info, filename, form_for, **kwargs):
        user_cache_keys = get_user_cache_keys(info.context.user.username)
        cache_key = user_cache_keys['photos']

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


# class VideoUploadMutation(Output, graphene.Mutation):
#     """Upload a video"""

#     class Arguments:
#         file = Upload(required=True)
#         form_for = PostFormFor(required=True)

#     filename = graphene.String()
#     base64_str = graphene.String()
#     mimetype = graphene.String()
     
#     @classmethod
#     @login_required
#     def mutate(cls, root, info, file: InMemoryUploadedFile, form_for, **kwargs):
#         user_cache_keys = get_user_cache_keys(info.context.user.username)
#         cache_photos_key, cache_video_key = user_cache_keys['photos'], user_cache_keys['video']

#         # Validate cache content
#         validate_cache_media(file, cache_photos_key, cache_video_key)

#         # Validate video file
#         try:
#             validate_post_video_file(file)
#         except ValidationError as err:
#             raise GraphQLError(
#                 err.message % (err.params or {}),
#                 extensions={'code': err.code}
#             )

#         # Use None so this value stays in the cache indefinitely, till explicitly deleted
#         # (or server restarts xD)
#         cache_key = cache_video_key
#         cache_video_dict = cache.get_or_set(cache_key, {}, None)

#         ## Save file to cache
#         # Get name without extension
#         # valid_filename = STORAGE.get_valid_name(file.name).split('.')[0]

#         # Get file extension and type to use with PIL
#         file_extension, ftype = get_image_file_thumbnail_extension_and_type(file)

#         # Save thumbnail to in-memory file as StringIO
#         image = Image.open(file)
#         # image = image.convert('RGB')
#         image.thumbnail(THUMBNAIL_ALIASES['']['sm_thumb']['size'], Image.ANTIALIAS)
#         thumb_file = BytesIO()
#         image.save(thumb_file, format=ftype)

#         # Use random uuid as filename so as to protect user privacy; and besides we don't
#         # really need the file name.
#         use_filename = str(uuid.uuid4()) + file_extension
#         # thumb_file.seek(0)

#         # Will be used with ContentFile to regenerate the file so as to save to
#         # model object when posting a post
#             # from django.core.files.base import ContentFile
#             # img_file = ContentFile(img_io.getvalue())
#             # saved_file_name = STORAGE.save(save_dir + valid_name, img_file)

#         file_bytes = thumb_file.getvalue()
#         base64_bytes = base64.b64encode(file_bytes)
#         base64_str = base64_bytes.decode('utf-8')
#         mimetype = file.content_type
#         # save_dir = FORM_AND_UPLOAD_DIR[form_for]
#         # saved_filename = STORAGE.save(save_dir + use_filename, file)

#         print(file.size, thumb_file.tell())
#         user_photos_list.append({
#             'file_bytes': file_bytes,
#             'filename': use_filename,
#             'mimetype': mimetype
#         })
#         cache.set(cache_key, user_photos_list)
#         thumb_file.close()

#         return SingleImageUploadMutation(
#             base64_str=base64_str,
#             filename=use_filename,
#             mimetype=mimetype
#         )
       
        