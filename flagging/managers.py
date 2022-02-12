from django.contrib.auth import get_user_model
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
        """Returns whether `model_obj` is FLAGGED or not"""
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

        # If there's a ValueError or TypeError, or the reason is not 
        # among the valid reasons, raise the ValidationError
        try:
            reason = int(reason)
            if reason in self.model.reason_values:
                return reason
            else:
                raise err
        except (ValueError, TypeError):
            raise err

    def create_flag(self, user, flag, reason):
        User = get_user_model()
        
        """
        Create a FlagInstance.
        Returns a dict {'created': bool} or raises ValidationError
        """
        # User shouldn't be able to flag his post.
        content_object = flag.content_object

        # If a user account is about to be flagged
        object_is_user = isinstance(content_object, User)

        # If a post is about to be flagged
        object_has_poster_id = hasattr(content_object, 'poster_id')

        # Validate object that's about to be flagged 
        # (should be user object or content with poster_id, let's say post)
        if not object_has_poster_id and not object_is_user:
            raise ValidationError(
                _("This object is not a User and doesn't have a poster_id attribute, hence can't be flagged"),
                code='invalid'
            )

        # If user wants to flag his post
        # (PS use object.poster_id not object.poster.id so as to minimize query)
        if object_has_poster_id and content_object.poster_id == user.id:
            raise ValidationError(
                _("You can't flag your own post"),
                code="can't_flag_own_post"
            )

        cleaned_reason = self._clean_reason(reason)
        try:
            flag_instance = self.create(flag=flag, user=user, reason=cleaned_reason)
            return {'created': True, 'flag_instance': flag_instance}
        except IntegrityError:
            raise ValidationError(
                _('This content has already been flagged by the user (%(user)s)'),
                params={'user': user},
                code='already_flagged_by_user'
            )

    def delete_flag(self, user, flag):
        """
        Delete flag instance
        Returns a dict {'deleted': bool} or raises ValidationError
        """
        try:
            flag_instance = self.get(user=user, flag=flag)
            instance_id = flag_instance.id
            flag_instance.delete()
            return {'deleted': True, 'flag_instance_id': instance_id}
        except self.model.DoesNotExist:
            raise ValidationError(
                _('This content has not been flagged by the user (%(user)s)'),
                params={'user': user},
                code='not_flagged_by_user'
            )

    def set_flag(self, user, model_obj, **kwargs):
        """Create or delete flag instance."""
        # Get flag of object via FlagMixin
        flag_obj = model_obj.flag
        reason = kwargs.get('reason', None)

        if reason:
            result = self.create_flag(user, flag_obj, reason)
        else:
            result = self.delete_flag(user, flag_obj)
        return result
