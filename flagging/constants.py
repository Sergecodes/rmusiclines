from decouple import config
from django.utils.translation import gettext_lazy as _


# If a post has this number of flags, it is considered FLAGGED
# and can be deleted by a moderator.
# TODO Moderators should also be able to notify a post for deletion by admin
# in case they deem a post inappropriate but can't yet delete it 
# coz it doesn't yet have the required number of flags.
# 
# Currently = 3
IS_FLAGGED_COUNT = config('IS_FLAGGED_COUNT', cast=int)


# If a post has this number of flags, it will automatically be deleted.
#
# Currently = 7
AUTO_DELETE_FLAGS_COUNT = config('AUTO_DELETE_FLAGS_COUNT', cast=int)



