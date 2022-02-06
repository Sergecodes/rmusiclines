from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from posts.constants import MAX_COMMENT_LENGTH


def validate_comment(comment: str):
    """Check if comment's length is appropriate"""
    
    if len(comment) > MAX_COMMENT_LENGTH:
        raise ValidationError(
            _('Comments should be less than %(max_length)s characters'),
            code='max_length',
            params={'max_length': MAX_COMMENT_LENGTH}
        )

