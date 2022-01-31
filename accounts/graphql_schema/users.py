import graphene
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from graphene_django import DjangoObjectType
from graphene_django_cud.mutations import DjangoPatchMutation
from graphql import GraphQLError
from graphql_auth import relay
from graphql_auth.bases import RelayMutationMixin, DynamicInputMixin
from graphql_jwt.decorators import login_required

from accounts.mixins import SendNewEmailActivationMixin, VerifyNewEmailMixin
from accounts.validators import UserUsernameValidator
from core.utils import PKMixin
# from posts.graphql_schema.artist_posts import ArtistPostType
# from posts.graphql_schema.non_artist_posts import NonArtistPostNode

User = get_user_model()


# Register the User model type else an arror will be raised
class UserType(PKMixin, DjangoObjectType):
    class Meta:
        model = User


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


class ChangeUsernameMutation(graphene.Mutation):
    """Change username of current logged in user(if they are permitted to change it"""

    class Arguments:
        new_username = graphene.String()

    success = graphene.Boolean()
    user = graphene.Field(UserType)

    @classmethod
    @login_required
    def mutate(cls, root, info, new_username):
        # Validate username
        UserUsernameValidator()(new_username)
        
        user = info.context.user

        try:
            user.change_username(new_username)
        except ValidationError as err:
            raise GraphQLError(
                err.message % err.params,
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


'''
class UserType(DjangoObjectType):
    is_suspended = graphene.Boolean(source='is_suspended')
    can_download = graphene.Boolean(source='can_download')
    can_change_username = graphene.Boolean(source='can_change_username')
    can_change_username_until_date = graphene.Boolean(
        source='can_change_username_until_date'
    )
    # private_artist_posts = graphene.List(source='private_artist_posts')
    private_non_artist_posts = graphene.List(NonArtistPostNode, source='private_non_artist_posts')
    # public_artist_posts
    public_non_artist_posts = graphene.List(NonArtistPostNode, source='public_non_artist_posts')
    # parent_artist_post_comments = 
    # parent_non_artist_post_comments

    class Meta:
        model = User
        exclude = [
            'profile_picture_width', 'profile_picture_height', 
            'cover_photo_width', 'cover_photo_height', 
        ]


class UserQuery(graphene.ObjectType):
    all_users = graphene.List(UserType)
    user_by_username = graphene.Field(
        UserType, 
        username=graphene.String(required=True)
    )

    def resolve_all_users(root, info):
        return User.objects.select_related(
            'pinned_non_artist_post',
            'pinned_artist_post'
        ).all()

    def resolve_user_by_username(root, info, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

'''




'''
from graphql_auth.bases import RelayMutationMixin, DynamicInputMixin, Output
from graphql_auth.decorators import verification_required
from graphql_auth.settings import graphql_auth_settings

from accounts.forms.users import UpdateUserForm


class UpdateAccountMixin(Output):
    """
    Update user model fields, defined on settings.

    User must be verified.
    """
    form = UpdateUserForm

    @classmethod
    @verification_required
    def resolve_mutation(cls, root, info, **kwargs):
        user = info.context.user
        f = cls.form(kwargs, instance=user)

        if f.is_valid():
            f.save()
            return cls(success=True)
        else:
            return cls(success=False, errors=f.errors.get_json_data())


class UpdateAccount(
    RelayMutationMixin, DynamicInputMixin, 
    UpdateAccountMixin, graphene.ClientIDMutation
):
    __doc__ = UpdateAccountMixin.__doc__
    _inputs = graphql_auth_settings.UPDATE_MUTATION_FIELDS
'''

