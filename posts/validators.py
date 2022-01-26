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


def validate_post_photo(post_photo):
    """
    Validate video file
    - Max size: 5mb
    - Types: png, jpg, gif

    :param `post_photo`: ArtistPostPhoto | NonArtistPostPhoto object
    """
    # TODO Also validate photo on server level(nginx, ...) before sending to django

    MAX_PHOTO_SIZE = 5242880
    VALID_CONTENT_TYPES = ['image/png', 'image/jpg', 'image/gif']

    file = post_photo.photo

    try:
        content_type = file.content_type
        if content_type in VALID_CONTENT_TYPES:
            if (file_size := file.size) > MAX_PHOTO_SIZE:
                raise ValidationError(
                    _('Please keep filesize under %s. Current filesize %s') % 
                    (filesizeformat(MAX_PHOTO_SIZE), filesizeformat(file_size)),
                    code='large_file'
                )
        else:
            raise ValidationError(
                _('Filetype not supported.'),
                code='invalid'
            )
    except AttributeError:
        pass


def validate_post_video(post_video):
    """
    Validate video file
    - Max size: 250mb
    - Max length: 6minutes(360s)
    - Min resolution: 32 x 32 px
    - Max resolution: 1920 x 1920 px
    - Types: mp4, mov

    :param `post_video`: ArtistPostVideo | NonArtistPostVideo object
    """

    MAX_VIDEO_SIZE, MAX_DURATION = 214958080, 360
    MIN_RESOLUTION, MAX_RESOLUTION = (32, 32), (1920, 1920)
    VALID_CONTENT_TYPES = ['video/mp4', 'video/mov']
    video = post_video.video
    
    try:
        content_type = video.content_type
        if content_type in VALID_CONTENT_TYPES:
            if (file_size := video.size) > MAX_VIDEO_SIZE:
                raise ValidationError(
                    _('Please keep filesize under %s. Current filesize %s') % 
                    (filesizeformat(MAX_VIDEO_SIZE), filesizeformat(file_size)),
                    code='large_file'
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
            _('Please keep duration under %s. Current duration %s and video time %s') % 
            (MAX_DURATION, duration, video_time),
            code='invalid'
        )

    # Validate resolution
    resolution = get_video_resolution(video)
    if resolution < MIN_RESOLUTION or resolution > MAX_RESOLUTION:
        raise ValidationError(
            _('Please keep resolution between %s and %s. Current resolution %s') % 
            (str(MIN_RESOLUTION), str(MAX_RESOLUTION), str(resolution)),
            code='invalid'
        )


