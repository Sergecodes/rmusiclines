import graphene
from django.contrib.auth import get_user_model, logout
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from graphene_django_cud.mutations import DjangoPatchMutation
from graphql import GraphQLError
from graphql_auth import relay
from graphql_auth.bases import RelayMutationMixin, DynamicInputMixin, Output
from graphql_auth.schema import UserNode

from accounts.mixins import SendNewEmailActivationMixin, VerifyNewEmailMixin
from accounts.validators import UserUsernameValidator
from core.decorators import verification_and_login_required
# Import(implicitly register) all types
from .types import *

User = get_user_model()


class PatchUserMutation(DjangoPatchMutation):
    class Meta:
        model = User
        login_required = True
        only_fields = [
            'display_name', 'country', 'birth_date', 'bio',
            'profile_picture', 'cover_photo', 'gender', 'is_mod', 
            'is_active', 'is_verified', 'is_premium', 'pinned_artist_post',
            'pinned_non_artist_post', 
        ]

    @classmethod
    def check_permissions(cls, root, info, input, id, obj: User):
        # Only current logged in user can update their account

        # The id used should be the pk not the global relay id
        if not isinstance(id, int):
            raise GraphQLError(
                _("Use the primary key of the user which is an integer; relay ids are not supported"),
                extensions={'code': 'invalid'}
            ) 

        print(info.context.user, info.context.user.pk)
        print(obj, obj.pk)
        if info.context.user.pk == obj.pk:
            return 
        else:
            raise GraphQLError(
                _("You can not modify another user's account"),
                extensions={'code': 'not_owner'}
            )


class ChangeUsernameMutation(graphene.Mutation, Output):
    """Change username of current logged in user(if they are permitted to change it)"""

    class Arguments:
        new_username = graphene.String()

    # The inherited class Output contains other appropriate return fields (success & errors)
    user = graphene.Field(UserNode)

    # The verification_required decorator from graphql_auth doesnt work here apparently,
    # so use custom permission verifier via user_passes_test.
    # Also, We use user_passes_test intead of login_required in the verify authenticated 
    # decorator to be able to provide a custom error message
    @classmethod
    @verification_and_login_required
    def mutate(cls, root, info, new_username):
        # Validate username
        UserUsernameValidator()(new_username)

        user = info.context.user
        
        try:
            user.change_username(new_username)
            # Note that user now has another username, so we should probably log them out
            logout(info.context)
        except ValidationError as err:
            raise GraphQLError(
                err.message % (err.params or {}),
                extensions={'code': err.code}
            )

        return ChangeUsernameMutation(user=user, success=True)


class ChangeEmailMutation(
    RelayMutationMixin, DynamicInputMixin, 
    SendNewEmailActivationMixin, graphene.ClientIDMutation
):
    __doc__ = SendNewEmailActivationMixin.__doc__
    _required_inputs = ['new_email', 'password']


class VerifyNewEmailMutation(
    RelayMutationMixin, DynamicInputMixin, 
    VerifyNewEmailMixin, graphene.ClientIDMutation
):
    __doc__ = VerifyNewEmailMixin.__doc__
    _required_inputs = ["token"]


class AuthRelayMutation(graphene.ObjectType):
    register = relay.Register.Field()
    verify_account = relay.VerifyAccount.Field()
    resend_activation_email = relay.ResendActivationEmail.Field()
    send_password_reset_email = relay.SendPasswordResetEmail.Field()
    password_reset = relay.PasswordReset.Field()
    password_set = relay.PasswordSet.Field() # For passwordless registration
    password_change = relay.PasswordChange.Field()
    delete_account = relay.DeleteAccount.Field()
    # archive_account = relay.ArchiveAccount.Field()
    # send_secondary_email_activation =  relay.SendSecondaryEmailActivation.Field()
    # verify_secondary_email = relay.VerifySecondaryEmail.Field()
    # swap_emails = relay.SwapEmails.Field()
    # remove_secondary_email = mutations.RemoveSecondaryEmail.Field()

    # django-graphql-jwt inheritances
    token_auth = relay.ObtainJSONWebToken.Field()
    verify_token = relay.VerifyToken.Field()
    refresh_token = relay.RefreshToken.Field()
    revoke_token = relay.RevokeToken.Field()


