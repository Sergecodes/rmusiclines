import datetime
import graphene
from django.contrib.auth import get_user_model, logout
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from graphene_django_cud.mutations import DjangoPatchMutation
from graphene_django_cud.util import disambiguate_id
from graphql import GraphQLError
from graphql_auth import relay as auth_relay
from graphql_auth.bases import RelayMutationMixin, DynamicInputMixin, Output
from graphql_auth.decorators import login_required
from graphql_auth.schema import UserNode

from accounts.mixins import SendNewEmailActivationMixin, VerifyNewEmailMixin
from accounts.models.users.models import Suspension
from accounts.validators import UserUsernameValidator
from flagging.graphql.types import *
from flagging.models.models import FlagInstance
# Import(implicitly register) all types
from .types import *

User = get_user_model()


class PatchUser(Output, DjangoPatchMutation):
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


class UserLogout(Output, graphene.ClientIDMutation):

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        # TODO: to log a user out, the JWT cookie should be deleted on the 
        # client's browser.

        request = info.context
        print(request.COOKIES)
        # Since JWT is stateless(no record of authentication is saved), 
        # to log user out, we simply delete the JWT cookie
        try:
            del request.COOKIES['JWT']
        except KeyError:
            pass

        print(request.COOKIES)

        return cls(success=False)


class ChangeUsername(Output, graphene.Mutation):
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
    @login_required
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

        return cls(user=user, success=True)


class ChangeEmail(
    RelayMutationMixin, DynamicInputMixin, 
    SendNewEmailActivationMixin, graphene.ClientIDMutation
):
    __doc__ = SendNewEmailActivationMixin.__doc__
    _required_inputs = ['new_email', 'password']


class VerifyNewEmail(
    RelayMutationMixin, DynamicInputMixin, 
    VerifyNewEmailMixin, graphene.ClientIDMutation
):
    __doc__ = VerifyNewEmailMixin.__doc__
    _required_inputs = ["token"]


class FollowUser(Output, graphene.ClientIDMutation):
    class Input:
        user_id = graphene.ID(required=True)

    user_follow = graphene.Field(UserFollowNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        follow_obj = user.follow_user(disambiguate_id(input['user_id']))

        return cls(user_follow=follow_obj)


class UnfollowUser(Output, graphene.ClientIDMutation):
    class Input:
        user_id = graphene.ID(required=True)

    follow_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        deleted_obj_id = user.unfollow_user(disambiguate_id(input['user_id']))

        return cls(follow_id=deleted_obj_id)


class BlockUser(Output, graphene.ClientIDMutation):
    class Input:
        user_id = graphene.ID(required=True)

    user_block = graphene.Field(UserBlockingNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        block_obj = user.block_user(disambiguate_id(input['user_id']))

        return cls(user_block=block_obj)


class UnblockUser(Output, graphene.ClientIDMutation):
    class Input:
        user_id = graphene.ID(required=True)

    block_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        deleted_obj_id = user.unblock_user(disambiguate_id(input['user_id']))

        return cls(block_id=deleted_obj_id)


class DeactivateAccount(Output, graphene.ClientIDMutation):
    class Input:
        user_id = graphene.ID(required=True)

    success = graphene.Boolean()
    account = graphene.Field(UserNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        user.deactivate()

        # Refresh from db to get updated records
        user.refresh_from_db()
        return cls(success=True, account=user)


class ReactivateAccount(Output, graphene.ClientIDMutation):
    class Input:
        user_id = graphene.ID(required=True)

    success = graphene.Boolean()
    account = graphene.Field(UserNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        user.reactivate()

        # Refresh from db to get updated records
        user.refresh_from_db()
        return cls(success=True, account=user)


class FlagUser(Output, graphene.ClientIDMutation):
    class Input:
        flag_user_id = graphene.ID(required=True)
        reason = graphene.Enum.from_enum(FlagInstance.FlagReason)

    flag_instance = graphene.Field(FlagInstanceNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user, flag_user_id = info.context.user, disambiguate_id(input['flag_user_id'])

        # Only moderator can flag user account
        if not user.is_mod:
            raise GraphQLError(
                _("You can not flag a user's account"),
                extensions={'code': 'not_permitted'}
            )

        flag_instance_obj = user.flag_object(User.active_users.get(id=flag_user_id), input['reason'])

        # TODO Notify staff


        return cls(flag_instance=flag_instance_obj)


class SuspendUser(Output, graphene.ClientIDMutation):
    class Input:
        suspend_user_id = graphene.ID(required=True)
        duration_in_days = graphene.Int()
        reason = graphene.String()

    suspension = graphene.Field(SuspensionNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        current_user, suspend_user_id = info.context.user, disambiguate_id(input['suspend_user_id'])
        
        # Only staff can suspend users
        if not current_user.is_staff:
            raise GraphQLError(
                _("You are not permitted to suspend a user's account"),
                extensions={'code': 'not_permitted'}
            )

        suspension_obj = Suspension(
            suspender=current_user,
            user=User.active_users.get(id=suspend_user_id),
            reason=input.get('reason', '')
        )

        if num_days := input.get('duration_in_days'):
            suspension_obj.duration = datetime.timedelta(days=num_days)
        
        suspension_obj.save()
        return cls(suspension=suspension_obj)


class Subscribe(Output, graphene.ClientIDMutation):
    """Subscribe to the platform(become a premium user)"""
    
    def mutate_and_get_payload(cls, root, info, **input):
        pass


class AuthRelayMutation(graphene.ObjectType):
    register = auth_relay.Register.Field()
    verify_account = auth_relay.VerifyAccount.Field()
    resend_activation_email = auth_relay.ResendActivationEmail.Field()
    send_password_reset_email = auth_relay.SendPasswordResetEmail.Field()
    password_reset = auth_relay.PasswordReset.Field()
    password_set = auth_relay.PasswordSet.Field() # For passwordless registration
    password_change = auth_relay.PasswordChange.Field()
    delete_account = auth_relay.DeleteAccount.Field()
    # archive_account = auth_relay.ArchiveAccount.Field()
    # send_secondary_email_activation =  auth_relay.SendSecondaryEmailActivation.Field()
    # verify_secondary_email = auth_relay.VerifySecondaryEmail.Field()
    # swap_emails = auth_relay.SwapEmails.Field()
    # remove_secondary_email = mutations.RemoveSecondaryEmail.Field()

    # django-graphql-jwt inheritances
    token_auth = auth_relay.ObtainJSONWebToken.Field()
    verify_token = auth_relay.VerifyToken.Field()
    refresh_token = auth_relay.RefreshToken.Field()
    revoke_token = auth_relay.RevokeToken.Field()


