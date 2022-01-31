from django.contrib.auth import get_user_model
from django.core.signing import SignatureExpired, BadSignature
from django.utils.translation import gettext as _
from django.utils.module_loading import import_string
from graphql_auth.bases import Output
from graphql_auth.constants import Messages, TokenAction
from graphql_auth.decorators import verification_required, password_confirmation_required
from graphql_auth.exceptions import UserNotVerified, TokenScopeError
from graphql_auth.models import UserStatus
from graphql_auth.utils import get_token_paylod
from graphql_auth.settings import graphql_auth_settings
from smtplib import SMTPException

from accounts.forms.users import ChangeEmailForm

User = get_user_model()

if graphql_auth_settings.EMAIL_ASYNC_TASK and \
    isinstance(graphql_auth_settings.EMAIL_ASYNC_TASK, str):
    async_email_func = import_string(graphql_auth_settings.EMAIL_ASYNC_TASK)
else:
    async_email_func = None


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

            # Add new email info to session
            session = info.context.session
            session[f'user-{current_user.username}-new-email'] = new_email
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
        payload = get_token_paylod(
            token, TokenAction.ACTIVATION, graphql_auth_settings.EXPIRATION_ACTIVATION_TOKEN
        )
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

            # No errors raised so we can safely get email from session and update user info
            session = info.context.session
            user_key = f'user-{info.context.user.username}-new-email'
            user.email = session.pop(user_key)
            user.save(update_fields=['email'])
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


