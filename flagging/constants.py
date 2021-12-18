from django.utils.translation import gettext_lazy as _


# reason displayed when flagging an object
FLAG_REASONS = [
	(1, _("Spam | Exists only to promote a service ")),
	(2, _("Abusive | Intended at promoting hatred")),
]
# number of flags before an object is marked as flagged
# after FLAG_ALLOWED flags, an object will be marked flagged.
# and moderators will now be able to delete it.
FLAGS_ALLOWED = 1
# new posts with this count are FLAGGED
IS_FLAGGED_COUNT = FLAGS_ALLOWED + 1