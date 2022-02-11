import graphene
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.signing import SignatureExpired, BadSignature
from django.utils.translation import gettext as _
from django.utils.module_loading import import_string
from graphql_auth.bases import Output
from graphql_auth.constants import Messages, TokenAction
from graphql_auth.decorators import verification_required, password_confirmation_required
from graphql_auth.exceptions import UserNotVerified, TokenScopeError
from graphql_auth.models import UserStatus
from graphql_auth.utils import get_token_paylod, revoke_user_refresh_token
from graphql_auth.settings import graphql_auth_settings
from smtplib import SMTPException

from accounts.forms.users import ChangeEmailForm
from accounts.models.artists.models import Artist

User = get_user_model()
EXPIRATION_ACTIVATION_TOKEN = timedelta(days=3)

if graphql_auth_settings.EMAIL_ASYNC_TASK and \
    isinstance(graphql_auth_settings.EMAIL_ASYNC_TASK, str):
    async_email_func = import_string(graphql_auth_settings.EMAIL_ASYNC_TASK)
else:
    async_email_func = None


class ArtistCUMutationMixin:
    """Artist Create-Update mutation mixin"""

    class Meta:
        model = Artist
        # Exclude the `tags` field coz graphql complaints that it doesn't
        # know how to convert(serialize) it 
        exclude_fields = ('tags', )
        # Ensure to use a name other than 'tags' else the tags will be 
        # sent to the corresponding model object as a list and will raise errors
        # when trying to save the object.
        custom_fields = {
            "artist_tags": graphene.List(graphene.String)
        }


class SendNewEmailActivationMixin(Output):
    """
    Send activation link to user's desired new email adress.
    
    This mixin should be protected(classes using it should ensure its methods
    make sure the user is logged in)
    """

    @classmethod
    @verification_required
    @password_confirmation_required
    def resolve_mutation(cls, root, info, **kwargs):
        current_user = info.context.user

        try:
            new_email = kwargs.get("new_email")
            form = ChangeEmailForm({"new_email": new_email})

            if form.is_valid():
                # Ensure user is actually using a new email and not the same email
                if new_email == current_user.email:
                    # This is the same format used by graphql_auth
                    error_message = [{
                        "message": _("This email is the same as your current email."),
                        "code": "same_email",
                    }]
                    return cls(success=False, errors=error_message)

                # Ensure no active user with this email exists
                user = User.objects.get(email=new_email, is_active=True)
                if user:
                    return cls(success=False, errors=Messages.EMAIL_IN_USE)
            else:
                return cls(success=False, errors=form.errors.get_json_data())

        except User.DoesNotExist:
            # No user owning this email is present, so user is permitted to use the email
            if async_email_func:
                async_email_func(current_user.status.send_activation_email, (info,))
            else:
                current_user.status.send_activation_email(info)

            # Add new email info to cache and set expiry date to activation token's expiry date
            # (don't use session so user can access the link via another browser for instance)
            cache_key = f'{current_user.username}-new-email'
            cache.set(cache_key, new_email, int(EXPIRATION_ACTIVATION_TOKEN.total_seconds()))
            return cls(success=True)  

        except SMTPException:
            return cls(success=False, errors=Messages.EMAIL_FAIL)
            

class VerifyNewEmailMixin(Output):
    """
    Verify user account and set user's email to the newly changed email.

    Receive the token that was sent by email.
    If the token is valid, change the user's email.
    """

    @classmethod
    def _verify(cls, token)-> User:
        # This payload is of the form:
        # {'username': users_username, 'action': TokenAction_to_perform}
        #
        # Default expiration is 7days(graphql_auth_settings.EXPIRATION_ACTIVATION_TOKEN). 
        # Let's use 3 days instead since it's a new email 
        # and user already has a valid email on the site...
        payload = get_token_paylod(token, TokenAction.ACTIVATION, EXPIRATION_ACTIVATION_TOKEN)
        user = User.objects.get(**payload)

        # Well let's just stick to the way graphql_auth does it by using the UserStatus
        # model to query for the status; rather than just doing 'user.status'.
        #
        # We could also directly use 'if not user.is_active' rather than 
        # 'if not user_status.verified'

        user_status = UserStatus.objects.get(user=user) 
        if not user_status.verified:  
            raise UserNotVerified

        return user

    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        try:
            token = kwargs.get("token")
            user = cls._verify(token)

            # No errors raised so we can safely get email from cache and update user info
            cache_key = f'{info.context.user.username}-new-email'
            new_email = cache.get(cache_key)

            # new_email will be None if key isn't in cache
            # (perhaps key has expired or already deleted)
            if not new_email:
                raise KeyError

            # Revoke previous refresh tokens since user has changed his email
            revoke_user_refresh_token(user)

            user.email = new_email
            user.save(update_fields=['email'])
            cache.delete(cache_key)
            return cls(success=True)
        except UserNotVerified:
            return cls(success=False, errors=Messages.NOT_VERIFIED)
        except SignatureExpired:
            return cls(success=False, errors=Messages.EXPIRED_TOKEN)
        except (BadSignature, TokenScopeError):
            return cls(success=False, errors=Messages.INVALID_TOKEN)
        except KeyError:
            # If new email isn't in session, that means the user has already used it
            # to verify his new email
            return cls(success=False, errors=Messages.ALREADY_VERIFIED)


