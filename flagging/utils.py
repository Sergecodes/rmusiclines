# from django.apps import apps
# FlagInstance = apps.get_model('flagging', 'FlagInstance')
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from flagging.models.models import FlagInstance


def process_flagging_request(*, user, model_obj, data: dict):
    """
    Process flagging request and return a response. This handles request for both Django and DRF

    Args:
        user ([type]): The logged in user
        model_obj ([type]): the object being flagged
        data (dict): the data received from the request

    Returns:
        [dict]: response has three keys:
            `status`(int): Zero indicates the request failed due to `ValidationError`.
            `msg`(str): response, success message in case request succeeds, reason for
            failure if it doesn't.

            **This key will only be present when request succeeds.**
            `flag`(int): Non-Zero(1) indicates that flag is created.
    """
    response = {'status': 0}

    try:
        result = FlagInstance.objects.set_flag(user, model_obj, **data)
        created, deleted = result.get('created'), result.get('deleted')

        # If new flag(flag instance) was created
        if created:
            response['msg'] = _(
                'The content has been flagged successfully. '
                'A moderator will review it shortly.'
            )
            response['flag'] = 1

        # If flag instance was deleted
        elif deleted:
            response['msg'] = _('The content has been unflagged successfully.')

        response.update({
            'status': 1
        })

    except ValidationError as e:
        response.update({
            'msg': e.messages
        })

    return response

