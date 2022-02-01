import datetime


## TODO Change constraint on database if any of these values is changed.
# ref. COPPA(Children's Online Privacy Protection Rule) RULES
USER_MIN_AGE = 13
# Oldest person alive in 2021 is 118 yrs old !
USER_MAX_AGE = 120
# Youngest music artist is probably 17
ARTIST_MIN_AGE = 15
# Oldest music artist is probably 95
ARTIST_MAX_AGE = 100


# After changing their username, the user must wait after this period of time
# before he can change it again.
USERNAME_CHANGE_WAIT_PERIOD = datetime.timedelta(days=15)


# The maximum number of posts that a non premium user
# can download in a month
NON_PREMIUM_USER_MAX_DOWNLOADS_PER_MONTH = 10


# Upload media directories
ARTISTS_PHOTOS_UPLOAD_DIR = 'artists_photos/'
USERS_PROFILE_PICTURES_UPLOAD_DIR = 'profile_pictures/'
USERS_COVER_PHOTOS_UPLOAD_DIR = 'cover_photos/'

