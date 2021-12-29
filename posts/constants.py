"""This file contains all the constants that will be used in this app"""

from datetime import timedelta

# After this number of minutes, comment/post can't be edited
COMMENT_CAN_EDIT_TIME_LIMIT = timedelta(minutes=3)
POST_CAN_EDIT_TIME_LIMIT = timedelta(minutes=3)

MAX_POST_LENGTH = 350

