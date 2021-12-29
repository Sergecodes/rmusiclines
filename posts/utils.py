"""This file contains utility functions"""

import re


def extract_hashtags(text):
    """
    Return a list containing the hashtags in `text`.
    It takes only alphanumeric characters(including underscores).
    """
    return re.findall(r'\B#\w*[a-zA-ZÀ-Ÿ]+\w*', text, re.UNICODE)

def extract_mentions(text):
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

