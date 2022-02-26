"""This file contains all the constants that will be used in this app"""
import os
from django.conf import settings


# class REPOST_TYPE(enum.Enum):
#     SIMPLE_REPOST = 'simple_repost'
#     NON_SIMPLE_REPOST = 'non_simple_repost'


# Maximum number of characters of a post and comment
MAX_POST_LENGTH = 500
MAX_COMMENT_LENGTH = 2000

# Maximum number of photos per post
MAX_NUM_PHOTOS = 4

# Audio cover image directory
POST_COVER_IMG_NAME = 'POST_COVER_IMG.png'
if settings.USE_S3:
    POST_COVER_IMG_DIR = os.path.join(
        settings.BASE_DIR, settings.STATIC_ROOT, 'posts/', settings.POST_COVER_IMG_NAME
    )
else:
    POST_COVER_IMG_DIR = os.path.join(
        settings.BASE_DIR, f'posts/{settings.STATIC_URL}/posts/', POST_COVER_IMG_NAME
    )


## Media upload directories
# To store temporary uploaded files that will certainly be soon deleted
TEMP_FILES_UPLOAD_DIR = 'tmp/'
ARTIST_POST_PHOTO_UPLOAD_DIR = 'artist_posts_photos/'
# Here, we'll store the video obtained from converting audio to video
ARTIST_POST_WAS_AUDIO_UPLOAD_DIR = 'artist_posts_was_audio_videos/'
ARTIST_POST_VIDEO_UPLOAD_DIR = 'artist_posts_videos/'
NON_ARTIST_POST_PHOTO_UPLOAD_DIR = 'non_artist_posts_photos/'
NON_ARTIST_POST_WAS_AUDIO_UPLOAD_DIR = 'non_artist_posts_was_audio_videos/'
NON_ARTIST_POST_VIDEO_UPLOAD_DIR = 'non_artist_posts_videos/'


# Initialise form upload dict(map form type to upload directory)
# In reality, the directory will be of the form 'user_2'/artist_posts_photos/ ... etc
FORM_AND_UPLOAD_DIR = {
    'artist_post_photo': ARTIST_POST_PHOTO_UPLOAD_DIR,
    'artist_post_audio': ARTIST_POST_WAS_AUDIO_UPLOAD_DIR,
    'artist_post_video': ARTIST_POST_VIDEO_UPLOAD_DIR,
    'non_artist_post_photo': NON_ARTIST_POST_PHOTO_UPLOAD_DIR,
    'non_artist_post_video': NON_ARTIST_POST_VIDEO_UPLOAD_DIR,
    'non_artist_post_audio': NON_ARTIST_POST_WAS_AUDIO_UPLOAD_DIR,

}

