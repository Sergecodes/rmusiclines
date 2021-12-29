from django.utils.translation import gettext_lazy as _


# Number of flags before an object is marked as flagged.
# After FLAG_ALLOWED flags, an object will be marked flagged.
# and moderators will now be able to delete it.
#
# Moderators should also be able to notify a post for deletion by admin
FLAGS_ALLOWED = 4
# Posts with this number of flags are considered FLAGGED
IS_FLAGGED_COUNT = FLAGS_ALLOWED + 1

