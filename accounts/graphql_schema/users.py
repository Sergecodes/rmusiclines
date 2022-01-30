import graphene
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from graphene_django import DjangoObjectType
from graphene_django_cud.mutations import DjangoPatchMutation
from graphql import GraphQLError
from graphql_auth import relay, mutations
from graphql_auth.bases import RelayMutationMixin, DynamicInputMixin, Output
from graphql_auth.decorators import verification_required
from graphql_auth.settings import graphql_auth_settings

from accounts.constants import USERNAME_CHANGE_WAIT_PERIOD
from accounts.forms.users import UpdateUserForm
from core.utils import PKMixin
# from posts.graphql_schema.artist_posts import ArtistPostType
# from posts.graphql_schema.non_artist_posts import NonArtistPostNode

User = get_user_model()



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
        # Only current user can change their account, 
        # (and super user for now)

        # The id used should be the pk not the global relay id
        # if not isinstance(id, int):
        #     raise GraphQLError(
        #         _("Use the primary key of the user which is an integer; relay ids are not supported"),
        #         extensions={
        #             'code': "invalid"
        #         }
        #     ) 

        # Only logged in user is permitted to update their account
        if info.context.user.pk == obj.pk:
            return 
        else:
            raise GraphQLError(
                _("You can only update your account"),
                extensions={
                    'code': "not_owner"
                }
            )


class ChangeUsernameMutation(DjangoPatchMutation):
    class Meta:
        model = User
        login_required = True
        # exclude_fields = ['id']
        only_fields = ['username']
        type_name = 'ChangeUsernameInput'

    @classmethod
    def before_save(cls, root, info, input, id, obj: User):
        if not obj.can_change_username:
            raise GraphQLError(
                _(
					"You cannot change your username until the %s; "
					"you need to wait %s days after changing your username."
					%(
                        str(obj.can_change_username_until_date), 
                        str(USERNAME_CHANGE_WAIT_PERIOD)
                    )
				),
                extensions={
                    'code': "can't_change_username_yet"
                }
            )

        # Update last changed username date
        obj.last_changed_username_on = timezone.now()
        return obj


class AuthRelayMutation(graphene.ObjectType):
    register = relay.Register.Field()
    verify_account = relay.VerifyAccount.Field()
    resend_activation_email = relay.ResendActivationEmail.Field()
    send_password_reset_email = relay.SendPasswordResetEmail.Field()
    password_reset = relay.PasswordReset.Field()
    password_set = relay.PasswordSet.Field() # For passwordless registration
    password_change = relay.PasswordChange.Field()
    # update_account = relay.UpdateAccount.Field()
    update_account = UpdateAccount.Field()
    # archive_account = relay.ArchiveAccount.Field()
    delete_account = relay.DeleteAccount.Field()
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
