''' Django notifications signal file '''
# -*- coding: utf-8 -*-
from django.dispatch import Signal

notify = Signal()

## apparently, this argument `providing_args` is deprecated.
# notify = Signal(providing_args=[  # pylint: disable=invalid-name
#     'recipient', 'actor', 'verb', 'action_object', 'target', 'description',
#     'timestamp', 'level', 
#     'category', 'follow_url', 'absolved'
# ])
