from django.conf import settings
from django.utils.translation import gettext_lazy as _


# If a post has this number of flags, it is considered FLAGGED
# and can be deleted by a moderator.
# TODO Moderators should also be able to notify a post for deletion by admin
# in case they deem a post inappropriate but can't yet delete it 
# coz it doesn't yet have the required number of flags.
# 
# Currently = 3
CONTENT_IS_FLAGGED_COUNT = settings.CONTENT_IS_FLAGGED_COUNT
# Currently = 2 and i think its okay. 2 mods can't lie lol
USER_IS_FLAGGED_COUNT = settings.USER_IS_FLAGGED_COUNT


# If a post has this number of flags, it will automatically be deleted.
#
# Currently = 7
AUTO_DELETE_FLAGS_COUNT = settings.AUTO_DELETE_FLAGS_COUNT
# Currently = 4
AUTO_SUSPEND_USER_ACCOUNT_FLAGS_COUNT = settings.AUTO_SUSPEND_USER_ACCOUNT_FLAGS_COUNT


