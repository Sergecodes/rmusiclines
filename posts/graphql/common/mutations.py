import base64
import graphene
import os
import uuid
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from graphql_auth.bases import Output
from graphql_auth.decorators import login_required
from io import BytesIO
from PIL import Image
from pydub import AudioSegment
import subprocess

from core.constants import FILE_STORAGE_CLASS
from core.utils import (
    get_file_extension, get_user_cache_keys,
    get_image_file_thumbnail_extension_and_type, get_file_path
)
from posts.constants import MAX_NUM_PHOTOS, TEMP_FILES_UPLOAD_DIR
from posts.validators import (
    validate_post_photo_file, validate_cache_media,
    validate_post_video_file, validate_post_audio_file
)

STORAGE = FILE_STORAGE_CLASS()
MEDIA_ROOT = settings.MEDIA_ROOT
THUMBNAIL_ALIASES = settings.THUMBNAIL_ALIASES

        
class MultipleImageUploadMutation(Output, graphene.Mutation):
    """Upload multiple images at once"""

    class Arguments:
        files = graphene.List(Upload, required=True)

    filenames = graphene.List(graphene.String)
    base64_strs = graphene.List(graphene.String)
    mimetypes = graphene.List(graphene.String)
     
    @classmethod
    @login_required
    def mutate(cls, root, info, files: list, **kwargs):
        user_cache_keys = get_user_cache_keys(info.context.user.username)
        cache_photos_key, cache_video_key = user_cache_keys['photos'], user_cache_keys['video']

        # Validate cache content and uploaded file
        for file in files:
            validate_cache_media(cache_photos_key, cache_video_key)

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
            
            use_filename = str(uuid.uuid4()) + '.' + file_extension
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

    @classmethod
    @login_required
    def mutate(cls, root, info, filename, **kwargs):
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


class VideoUploadMutation(Output, graphene.Mutation):
    """
    Upload a video.
    Flow:
        - Video is uploaded to backend. 
        - If AWS Elastic video transcoder is activated, call their api to compress video 
        and get result(perhaps url and filename); else save video(compressing with ffmpeg seems slow)
        and get result...
        - Store filename, mimetype and url in cache and return them.
    """

    class Arguments:
        file = Upload(required=True)

    filename = graphene.String()
    url = graphene.String()
    mimetype = graphene.String()
     
    @classmethod
    @login_required
    def mutate(cls, root, info, file, **kwargs):
        ## Note that InMemoryUploaded files will be saved during validation,
        # while TemporaryUploaded files won't be

        user = info.context.user
        user_cache_keys = get_user_cache_keys(user.username)
        cache_photos_key, cache_video_key = user_cache_keys['photos'], user_cache_keys['video']

        # Validate cache content
        validate_cache_media(cache_photos_key, cache_video_key)

        # Validate video file.
        try:
            validate_post_video_file(file)
        except ValidationError as err:
            raise GraphQLError(
                err.message % (err.params or {}),
                extensions={'code': err.code}
            )

        # Use None so this value stays in the cache indefinitely, till explicitly deleted
        # (or server restarts xD)
        cache_key = cache_video_key
        # cache_video_dict = cache.get_or_set(cache_key, {}, None)


        # TODO Call external api (aws elastic video encoder) to compress video


        use_filename = str(uuid.uuid4()) + '.' + get_file_extension(file)
        mimetype = file.content_type
        save_path = os.path.join(MEDIA_ROOT, TEMP_FILES_UPLOAD_DIR, file.name)

        # If file is not in disk, save it. This is the case for TemporaryUploadedFiles.
        if not STORAGE.exists(save_path):
            print('not in storage')
            saved_filename = STORAGE.save(TEMP_FILES_UPLOAD_DIR + use_filename, file)
            url = STORAGE.url(saved_filename)

        # Else if file is already in disk, rename it with custom name. 
        # This is the case for InMemoryUploadedFiles coz during validation, they need to be
        # saved to get duration, resolution, etc...
        else:
            print('in storage')
            new_save_path = os.path.join(MEDIA_ROOT, TEMP_FILES_UPLOAD_DIR, use_filename)
            os.rename(save_path, new_save_path)
            url = STORAGE.url(TEMP_FILES_UPLOAD_DIR + use_filename)

        file_dict = {'filename': use_filename, 'mimetype': mimetype, 'url': url}
        cache.set(cache_key, file_dict, None)

        return VideoUploadMutation(**file_dict)
       

class AudioUploadMutation(Output, graphene.Mutation):
    """
    Upload an audio.
    Flow:
        - Audio is uploaded to backend. 
        - Compress audio(perhaps use bitrate 96k) then convert to video using custom image/images
        - If AWS Elastic video transcoder is activated, call their api to compress video 
        and get result(perhaps url and filename); else save video(compressing with ffmpeg seems slow)
        and get result...
        - Store filename, mimetype and url in cache and return them.
    """

    class Arguments:
        file = Upload(required=True)

    filename = graphene.String()
    url = graphene.String()
    mimetype = graphene.String()
     
    @classmethod
    @login_required
    def mutate(cls, root, info, file, **kwargs):
        user = info.context.user
        user_cache_keys = get_user_cache_keys(user.username)
        cache_photos_key, cache_video_key = user_cache_keys['photos'], user_cache_keys['video']

        # Validate cache content
        validate_cache_media(cache_photos_key, cache_video_key)

        # Validate audio file
        try:
            validate_post_audio_file(file)
        except ValidationError as err:
            raise GraphQLError(
                err.message % (err.params or {}),
                extensions={'code': err.code}
            )

        # Use None so this value stays in the cache indefinitely, till explicitly deleted
        # (or server restarts xD)
        cache_key = cache_video_key
    
        # TODO Compress audio 
        compressed_audio_path = os.path.join(settings.MEDIA_ROOT, TEMP_FILES_UPLOAD_DIR, file.name)
        audio = AudioSegment.from_mp3(get_file_path(file))
        output = audio.export(compressed_audio_path, bitrate='92k')
        print(type(output))

        # TODO Convert to video
        audio_path = ''
        cover_image_path = ''
        output_video_path = ''  # /.../.../foo.mp4
        process = subprocess.run(
            'ffmpeg', '-loop', 1, '-i', 
            cover_image_path, '-i', audio_path, 
            '-c:a', 'copy', '-c:v', 'libx264', 
            '-shortest', output_video_path, shell=True
        )

        print(type(process.stdout))

        # TODO Call external api (aws elastic video encoder) to compress video
        

        use_filename = str(uuid.uuid4()) + '.' + get_file_extension(file)
        mimetype = file.content_type
        save_path = os.path.join(MEDIA_ROOT, TEMP_FILES_UPLOAD_DIR, file.name)

        # If file is not in disk, save it. This is the case for TemporaryUploadedFiles.
        if not STORAGE.exists(save_path):
            print('not in storage')
            saved_filename = STORAGE.save(TEMP_FILES_UPLOAD_DIR + use_filename, file)
            url = STORAGE.url(saved_filename)

        # Else if file is already in disk, rename it with custom name. 
        # This is the case for InMemoryUploadedFiles coz during validation, they need to be
        # saved to get duration, resolution, etc...
        else:
            print('in storage')
            new_save_path = os.path.join(MEDIA_ROOT, TEMP_FILES_UPLOAD_DIR, use_filename)
            os.rename(save_path, new_save_path)
            url = STORAGE.url(TEMP_FILES_UPLOAD_DIR + use_filename)

        file_dict = {'filename': use_filename, 'mimetype': mimetype, 'url': url}
        cache.set(cache_key, file_dict, None)

        return AudioUploadMutation(**file_dict)
       

class DeleteUploadedVideoMutation(Output, graphene.Mutation):
    """Delete uploaded video(remove it from cache)"""

    @classmethod
    @login_required
    def mutate(cls, root, info, **kwargs):
        user_cache_keys = get_user_cache_keys(info.context.user.username)
        cache.delete(user_cache_keys['video'])

        return DeleteUploadedVideoMutation(success=True)
