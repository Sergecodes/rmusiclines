from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _
from graphql import GraphQLError

from core.utils import get_file_extension
from posts.constants import MAX_NUM_PHOTOS
from .utils import get_video_duration, get_audio_duration, get_video_resolution

'''
File sizes:
    2.5MB - 2621440
    5MB - 5242880
    10MB - 10485760
    20MB - 20971520
    50MB - 52428800
    100MB - 104857600
    250MB - 262144000
    500MB - 524288000
'''


def validate_post_photo_file(photo_file):
    """
    Validate photo file
    - Max size: 20mb
    - Types: png, jpg, gif

    :param `photo_file`: File object
    """
    # TODO Also validate photo on server level(nginx, ...) before sending to django

    MAX_PHOTO_SIZE = 20971520
    VALID_CONTENT_TYPES = ['image/png', 'image/jpg', 'image/jpeg', 'image/gif']
    file = photo_file

    try:
        content_type = file.content_type

        if content_type in VALID_CONTENT_TYPES:
            # Verify if content type is same as extension. If it's not the same, that means
            # someone has surely tampered with the file extension(renamed it).
            if content_type in ['image/jpg', 'image/jpeg']:
                ctype_ext = 'jpg'
            else:
                ctype_ext = content_type.split('/')[-1]

            if ctype_ext != get_file_extension(file):
                raise ValidationError(
                    _("Corrupt file, content type doesn't match with extension"),
                    code='corrupt_file'
                )

            if (file_size := file.size) > MAX_PHOTO_SIZE:
                raise ValidationError(
                    _('Please keep filesize under %(max_photo_size)s. Current filesize %(photo_size)s'),
                    code='large_file',
                    params={
                        'max_photo_size': filesizeformat(MAX_PHOTO_SIZE),
                        'photo_size': filesizeformat(file_size)
                    }
                )
        else:
            raise ValidationError(
                _('Filetype %(ctype)s not supported.'),
                code='invalid',
                params={'ctype': content_type}
            )
    except AttributeError:
        pass


def validate_post_audio_file(audio_file):
    """
    Validate audio file
    - Max size: 10mb
    - Max duration: 3minutes(180)
    - Types: mp3

    :param `audio_file`: File object
    """

    MAX_AUDIO_SIZE, MAX_DURATION = 10485760, 180
    VALID_CONTENT_TYPES = ['audio/mpeg']
    audio = audio_file
    
    content_type = audio.content_type
    if content_type in VALID_CONTENT_TYPES:
        # Ensure file extension hasn't been tampered with.
        
        # Use mp3 since we only have audio/mpeg which corresponds to mp3
        ctype_ext = 'mp3'  
        if ctype_ext != get_file_extension(audio):
            raise ValidationError(
                _("Corrupt file, content type doesn't match with extension"),
                code='corrupt_file'
            )

        if (file_size := audio.size) > MAX_AUDIO_SIZE:
            raise ValidationError(
                _('Please keep filesize under %(max_audio_size)s. Current filesize %(audio_size)s'),
                code='large_file',
                params={
                    'max_audio_size': filesizeformat(MAX_AUDIO_SIZE),
                    'audio_size': filesizeformat(file_size)
                }
            )
    else:
        raise ValidationError(
            _('Filetype %(ctype)s not supported.'),
            code='invalid',
            params={'ctype': content_type}
        )

    # Validate duration
    duration, video_time = get_audio_duration(audio)
    if duration > MAX_DURATION:
        raise ValidationError(
            _('Please keep duration under %(max_duration)s. Current duration %(duration)s and video time %(time)s'),
            code='invalid',
            params={
                'max_duration': MAX_DURATION,
                'duration': duration,
                'time': video_time
            }
        )


def validate_post_video_file(video_file):
    """
    Validate video file
    - Max size: 250mb
    - Max length: 6minutes(360s)
    - Min resolution: 32 x 32 px
    - Max resolution: 1920 x 1920 px
    - Types: mp4, mov

    :param `video_file`: File object
    """

    MAX_VIDEO_SIZE, MAX_DURATION = 262144000, 360
    MIN_RESOLUTION, MAX_RESOLUTION = [32, 32], [1920, 1920]
    VALID_CONTENT_TYPES = ['video/mp4', 'video/mov']
    video = video_file
    
    content_type = video.content_type
    if content_type in VALID_CONTENT_TYPES:
        # Ensure content type matches extension
        ctype_ext = content_type.split('/')[-1]
        if ctype_ext != get_file_extension(video):
            raise ValidationError(
                _("Corrupt file, content type doesn't match with extension"),
                code='corrupt_file'
            )

        if (file_size := video.size) > MAX_VIDEO_SIZE:
            raise ValidationError(
                _('Please keep filesize under %(max_video_size)s. Current filesize %(video_size)s'),
                code='large_file',
                params={
                    'max_video_size': filesizeformat(MAX_VIDEO_SIZE),
                    'video_size': filesizeformat(file_size)
                }
            )
    else:
        raise ValidationError(
            _('Filetype %(ctype)s not supported.'),
            code='invalid',
            params={'ctype': content_type}
        )

    # Validate resolution
    resolution = get_video_resolution(video)
    if resolution < MIN_RESOLUTION or resolution > MAX_RESOLUTION:
        raise ValidationError(
            _('Please keep resolution between %(min_resolution)s and %(max_resolution)s. Current resolution %(resolution)s'),
            code='invalid',
            params={
                'min_resolution': MIN_RESOLUTION,
                'max_resolution': MAX_RESOLUTION,
                'resolution': resolution
            }
        )

    # Validate video duration
    # duration, video_time = get_video_duration(video)
    # if duration > MAX_DURATION:
    #     raise ValidationError(
    #         _('Please keep duration under %(max_duration)s. Current duration %(duration)s and video time %(time)s'),
    #         code='invalid',
    #         params={
    #             'max_duration': MAX_DURATION,
    #             'duration': duration,
    #             'time': video_time
    #         }
    #     )


def validate_cache_media(cache_photos_key: str, cache_video_key: str):
    """
    Validate cache media; cache can only contain either only a GIF or only a video or a given
    maximum number of photos. 
    This function verifies if we can go ahead and upload a media file and it is use in the file
    upload mutations.
    """

    # Verify if video is present
    video_dict = cache.get(cache_video_key, {})
    if video_dict:
        raise GraphQLError(
            _('Video already uploaded'),
            extensions={'code': 'invalid'}
        )

    photos_list = cache.get(cache_photos_key, [])

    # Verify if GIF is present
    photo_extensions = [get_file_extension(photo_dict['filename']) for photo_dict in photos_list]
    if 'gif' in photo_extensions:
        raise GraphQLError(
            _('GIF already uploaded'),
            extensions={'code': 'invalid'}
        )
    
    # Validate photos length
    if len(photos_list) == MAX_NUM_PHOTOS:
        raise GraphQLError(
            _('Maximum number of photos attained'),
            extensions={'code': 'max_photos_attained'}
        )

