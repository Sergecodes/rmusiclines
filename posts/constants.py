"""This file contains all the constants that will be used in this app"""
from datetime import timedelta


# class REPOST_TYPE(enum.Enum):
#     SIMPLE_REPOST = 'simple_repost'
#     NON_SIMPLE_REPOST = 'non_simple_repost'


# After this number of minutes, comment/post can't be edited
COMMENT_CAN_EDIT_TIME_LIMIT = timedelta(minutes=3)
POST_CAN_EDIT_TIME_LIMIT = timedelta(minutes=3)


# Maximum number of characters of a post and comment
MAX_POST_LENGTH = 350
MAX_COMMENT_LENGTH = 2000

# Maximum number of photos per post
MAX_NUM_PHOTOS = 4


# Media upload directories
ARTIST_POSTS_PHOTOS_UPLOAD_DIR = 'artist_posts_photos/'
NON_ARTIST_POSTS_PHOTOS_UPLOAD_DIR = 'non_artist_posts_photos/'
ARTIST_POSTS_VIDEOS_UPLOAD_DIR = 'artist_posts_videos/'
NON_ARTIST_POSTS_VIDEOS_UPLOAD_DIR = 'non_artist_posts_videos/'


# Initialise form upload dict(map form type to upload directory)
FORM_AND_UPLOAD_DIR = {
    'artist_post_photo': ARTIST_POSTS_PHOTOS_UPLOAD_DIR,
    'non_artist_post_photo': NON_ARTIST_POSTS_PHOTOS_UPLOAD_DIR,
    'artist_post_video': ARTIST_POSTS_VIDEOS_UPLOAD_DIR,
    'non_artist_post_video': NON_ARTIST_POSTS_VIDEOS_UPLOAD_DIR,

}

