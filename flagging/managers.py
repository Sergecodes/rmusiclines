from django.core.exceptions import ValidationError
from django.db import IntegrityError, models
from django.utils.translation import gettext_lazy as _
 
from core.utils import get_content_type


class FlagManager(models.Manager):
    def get_flag(self, model_obj):
        ctype = get_content_type(model_obj)
        # All flaggable models should have a `poster` attribute
        # or property at least 
      
        flag, created = self.get_or_create(
            content_type=ctype, 
            object_id=model_obj.pk, 
            defaults={'creator': model_obj.poster}
        )
        return flag

    def is_flagged(self, model_obj):
        flag = self.get_flag(model_obj)
        return flag.is_flagged

    def has_flagged(self, user, model_obj):
        """
        Returns whether a model object has been flagged by a user or not

        Args:
            user (object): the user to be inquired about.
            model_obj (object): the model object to be inquired upon.

        Returns:
            bool
        """
        return model_obj.flags.filter(user=user).exists()


class FlagInstanceManager(models.Manager):
    def _clean_reason(self, reason):
        """Ensure that a valid flagging reason is used"""
        err = ValidationError(
                _('%(reason)s is an invalid reason'),
                params={'reason': reason},
                code='invalid'
                )
        try:
            reason = int(reason)
            if reason in self.model.reason_values:
                return reason
            raise err

        except (ValueError, TypeError):
            raise err

    def _clean(self, reason, info):
        cleaned_reason = self._clean_reason(reason)
        cleaned_info = None

        # If reason is set to last value (`100 - Something else`)
        # and no extra info is passed, raise error
        if cleaned_reason == self.model.reason_values[-1]:
            cleaned_info = info
            if not cleaned_info:
                raise ValidationError(
                    _('Please supply some information as the reason for flagging'),
                    params={'info': info},
                    code='required'
                )
        return cleaned_reason, cleaned_info

    def create_flag(self, user, flag, reason, info):
        """Create a FlagInstance"""
        # user shouldn't be able to flag his post
        # get poster_id not poster.id so as to minimize query
        content_object = flag.content_object

        if not hasattr(content_object, 'poster_id'):
            raise ValidationError(
                _("This object doesn't have a poster_id")
            )
            # return {'created': False, 'msg': _("This object doesn't have a poster_id")}

        if content_object.poster_id == user.id:
            # print("You can't flag your post")
            return {'created': False, 'msg': _("You can't flag your own post.")}

        cleaned_reason, cleaned_info = self._clean(reason, info)
        try:
            self.create(flag=flag, user=user, reason=cleaned_reason, info=cleaned_info)
            return {'created': True}

        except IntegrityError:
            raise ValidationError(
                    _('This content has already been flagged by the user (%(user)s)'),
                    params={'user': user},
                    code='invalid'
                )

    def delete_flag(self, user, flag):
        """Delete flag instance"""
        try:
            self.get(user=user, flag=flag).delete()
            return {'deleted': True}

        except self.model.DoesNotExist:
            raise ValidationError(
                _('This content has not been flagged by the user (%(user)s)'),
                params={'user': user},
                code='invalid'
            )

    def set_flag(self, user, model_obj, **kwargs):
        """Create or delete flag instance."""
        # Get flag of object via FlagMixin
        flag_obj = model_obj.flag
        info = kwargs.get('info', None)
        reason = kwargs.get('reason', None)

        if reason:
            result = self.create_flag(user, flag_obj, reason, info)
        else:
            result = self.delete_flag(user, flag_obj)
        return result
