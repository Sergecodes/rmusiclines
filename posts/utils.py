"""This file contains utility functions"""

import cv2
import datetime
import re


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


def get_video_duration(video)-> tuple[int, str]:
    """
    Get duration of `video` in seconds and video_time.
    `video`: video File object
    """
     
    capture_obj = cv2.VideoCapture(video)
    frames = capture_obj.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = int(capture_obj.get(cv2.CAP_PROP_FPS))

    # Calculate duration of video in seconds
    duration = frames // fps
    # Calculate time of video eg. 0:00:28
    video_time = str(datetime.timedelta(seconds=duration))  

    return (duration, video_time)


def get_video_resolution(video)-> tuple[int, int]:
    """
    Get resolution(width, height) of video
    `video`: video File object
    """
    capture_obj = cv2.VideoCapture(video)
    width = capture_obj.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = capture_obj.get(cv2.CAP_PROP_FRAME_HEIGHT)

    return (width, height)

