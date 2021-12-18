import uuid
from django import template
from django.utils.translation import gettext_lazy as _

from flagging.models import Flag, FlagInstance

register = template.Library()


def get_app_name(obj):
    return type(obj)._meta.app_label


def get_model_name(obj):
    return type(obj).__name__


@register.filter
def has_flagged(user, obj):
    if user.is_authenticated:
        return Flag.objects.has_flagged(user, obj)

    return False


@register.inclusion_tag('flag/flag_form.html')
def render_flag_form(obj, user, request, display_title=False):
    """
    A template tag used for adding flag form in templates 
    to render the flag form for a post model inside the app posts

    Usage: `{% render_flag_form post user request %}`
    """

    ## verify if flag form should be displayed
    ## no need for this, since we already determine this in the parent(invoking) template
    # obj_model_name = get_model_name(obj)

    # SocialProfiles can't be flagged
    # if obj_model_name == 'SocialProfile':
    #     should_display = False
    # elif user.is_anonymous:
    #     should_display = False

    # # user can't flag his own post
    # elif hasattr(obj, 'poster_id') and obj.poster_id != user.id:
    #     should_display = True
    # else:
    #     should_display = False

    return {
        # generate random id for each modal
        # which will be used in areas where there are inputs linked to labels via ids. 
        # see flag_form form.
        'random_uid': str(uuid.uuid4()).split('-')[0],
        'app_name': get_app_name(obj),
        'model_name': get_model_name(obj),
        'model_id': obj.id,
        'user': user,
        'has_flagged': has_flagged(user, obj),
        'num_flags': Flag.objects.get_flag(obj).count,
        'flag_reasons': FlagInstance.reasons,
        'request': request,
        'display_title': display_title,
    }
    

