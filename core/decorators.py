from django.utils.translation import gettext_lazy as _
from graphql_jwt.decorators import user_passes_test
from graphql_jwt.exceptions import PermissionDenied


verification_and_login_required = user_passes_test(
    lambda user: user.is_authenticated and user.status.verified,
    PermissionDenied({
        'message': _("You need to be logged in and your account status verified"),
        'code': 'unauthenticated_or_not_verified'
    })
)


