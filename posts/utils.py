"""This file contains utility functions"""

import datetime
import os
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from moviepy.editor import VideoFileClip, AudioFileClip

from core.utils import get_file_path


def extract_hashtags(text)-> list:
    """
    Return a list containing the hashtags in `text`.
    It takes only alphanumeric characters(including underscores).
    """
    hashtag_list_with_hash = re.findall(r'\B#\w*[a-zA-ZÀ-Ÿ]+\w*', text, re.UNICODE)
    return [hashtag_name.replace('#', '') for hashtag_name in hashtag_list_with_hash]


def extract_mentions(text)-> list:
    """
    Return a list containing the usernames in `text`;
    Remember usernames should be between {1,15} characters and alphanumeric(\w)
    """
    INVALID_USERNAME_LENGTH_THRESHOLD = 16
    
    # Get strings of length 16 too so that if any username of length 16 is obtained
    # we know it is invalid
    result = re.findall(r"(^|[^@\w])@(\w{1,16})", text, re.UNICODE)
    usernames = [tuple[1] for tuple in result if len(tuple) != INVALID_USERNAME_LENGTH_THRESHOLD]

    return usernames


def get_post_media_upload_path(poster_id, folder_dir, filename):
    """File will be uploaded to MEDIA_ROOT/users/user_<poster_id>/<folder_dir>/<filename>"""
    return os.path.normpath('users/user_{0}/{1}/{2}'.format(poster_id, folder_dir, filename))


def get_audio_duration(audio)-> tuple[int, str]:
    """
    Get duration of `audio` in seconds and audio_time.
    `audio`: audio File object
    """
    duration = round(AudioFileClip(get_file_path(audio)).duration)

    # Calculate time of audio eg. 0:00:28
    audio_time = str(datetime.timedelta(seconds=duration))  

    return duration, audio_time


def get_video_duration(video)-> tuple[int, str]:
    """
    Get duration of `video` in seconds and video_time.
    `video`: video File object
    """

    duration = round(VideoFileClip(get_file_path(video)).duration)

    # Calculate time of video eg. 0:00:28
    video_time = str(datetime.timedelta(seconds=duration))  

    return duration, video_time


def get_video_resolution(video)-> tuple[int, int]:
    """
    Get resolution(width, height) of video
    `video`: video File object
    """
    return VideoFileClip(get_file_path(video)).size


def get_artist_post(post_or_id):
    """If int is passed, get corresponding artist post. Else return post"""
    from posts.models.artist_posts.models import ArtistPost

    if isinstance(post_or_id, int):
        id = post_or_id
        return ArtistPost.objects.get(id=id)
    elif isinstance(post_or_id, ArtistPost):
        post = post_or_id
        return post
    else:
        raise ValidationError(
            _('Invalid type'),
            code='invalid'
        )


def get_artist_post_comment(comment_or_id):
    """If int is passed, get corresponding artist post comment. Else return comment"""
    from posts.models.artist_posts.models import ArtistPostComment

    if isinstance(comment_or_id, int):
        id = comment_or_id
        return ArtistPostComment.objects.get(id=id)
    elif isinstance(comment_or_id, ArtistPostComment):
        comment = comment_or_id
        return comment
    else:
        raise ValidationError(
            _('Invalid type'),
            code='invalid'
        )


def get_non_artist_post_comment(comment_or_id):
    """If int is passed, get corresponding artist post comment. Else return comment"""
    from posts.models.artist_posts.models import NonArtistPostComment

    if isinstance(comment_or_id, int):
        id = comment_or_id
        return NonArtistPostComment.objects.get(id=id)
    elif isinstance(comment_or_id, NonArtistPostComment):
        comment = comment_or_id
        return comment
    else:
        raise ValidationError(
            _('Invalid type'),
            code='invalid'
        )


def get_non_artist_post(post_or_id):
    """If int is passed, get corresponding non artist post. Else return post"""

    from posts.models.non_artist_posts.models import NonArtistPost

    if isinstance(post_or_id, int):
        id = post_or_id
        return NonArtistPost.objects.get(id=id)
    elif isinstance(post_or_id, NonArtistPost):
        post = post_or_id
        return post
    else:
        raise ValidationError(
            _('Invalid type'),
            code='invalid'
        )

