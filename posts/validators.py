from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _

from .utils import get_video_duration, get_video_resolution

'''
File sizes:
    2.5MB - 2621440
    5MB - 5242880
    10MB - 10485760
    20MB - 20971520
    50MB - 52428800
    100MB - 104857600
    250MB - 214958080
    500MB - 429916160
'''


def validate_post_photo_file(photo_file):
    """
    Validate photo file
    - Max size: 5mb
    - Types: png, jpg, gif

    :param `photo_file`: File object
    """
    # TODO Also validate photo on server level(nginx, ...) before sending to django

    MAX_PHOTO_SIZE = 5242880
    VALID_CONTENT_TYPES = ['image/png', 'image/jpg', 'image/jpeg', 'image/gif']
    file = photo_file

    try:
        content_type = file.content_type
        if content_type in VALID_CONTENT_TYPES:
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
                _('Filetype not supported.'),
                code='invalid'
            )
    except AttributeError:
        pass


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

    MAX_VIDEO_SIZE, MAX_DURATION = 214958080, 360
    MIN_RESOLUTION, MAX_RESOLUTION = (32, 32), (1920, 1920)
    VALID_CONTENT_TYPES = ['video/mp4', 'video/mov']
    video = video_file
    
    try:
        content_type = video.content_type
        if content_type in VALID_CONTENT_TYPES:
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
                _('Filetype not supported.'),
                code='invalid'
            )
    except AttributeError:
        pass

    # Validate video duration
    duration, video_time = get_video_duration(video)
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


# def validate_post_photo(post_photo):
#     """Validate post photo instance"""
#     validate_post_photo_file(post_photo.file)


# def validate_post_video(post_video):
#     """Validate post video instance"""
#     validate_post_video_file(post_video.file)


