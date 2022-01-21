import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType
from graphql_auth import relay, mutations
# from posts.graphql_schema.artist_posts import ArtistPostType
from posts.graphql_schema.non_artist_posts import NonArtistPostNode

User = get_user_model()


class AuthRelayMutation(graphene.ObjectType):
    register = relay.Register.Field()
    verify_account = relay.VerifyAccount.Field()
    resend_activation_email = relay.ResendActivationEmail.Field()
    send_password_reset_email = relay.SendPasswordResetEmail.Field()
    password_reset = relay.PasswordReset.Field()
    password_set = relay.PasswordSet.Field() # For passwordless registration
    password_change = relay.PasswordChange.Field()
    update_account = relay.UpdateAccount.Field()
    archive_account = relay.ArchiveAccount.Field()
    delete_account = relay.DeleteAccount.Field()
    send_secondary_email_activation =  relay.SendSecondaryEmailActivation.Field()
    verify_secondary_email = relay.VerifySecondaryEmail.Field()
    swap_emails = relay.SwapEmails.Field()
    remove_secondary_email = mutations.RemoveSecondaryEmail.Field()

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
