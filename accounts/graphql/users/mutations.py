import base64
import datetime
import graphene
import uuid
from actstream.actions import follow, unfollow
from django.conf import settings
from django.contrib.auth import get_user_model, logout
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from graphene_django_cud.mutations import DjangoPatchMutation
from graphene_django_cud.util import disambiguate_id
from graphql import GraphQLError
from graphql_auth import relay as auth_relay
from graphql_auth.bases import RelayMutationMixin, DynamicInputMixin, Output
from graphql_auth.decorators import login_required
from graphql_auth.schema import UserNode
from graphql_auth.utils import revoke_user_refresh_token
from graphene_file_upload.scalars import Upload
from io import BytesIO
from PIL import Image

from accounts.constants import USERS_COVER_PHOTOS_UPLOAD_DIR, USERS_PROFILE_PICTURES_UPLOAD_DIR
from accounts.mixins import SendNewEmailActivationMixin, VerifyNewEmailMixin
from accounts.models.users.models import Suspension
from accounts.validators import UserUsernameValidator, validate_profile_and_cover_photo
from core.constants import FILE_STORAGE_CLASS
from core.utils import get_image_file_thumbnail_extension_and_type
from posts.utils import get_post_media_upload_path
from flagging.graphql.types import FlagInstanceNode, FlagReason
from notifications.models.models import Notification
from notifications.signals import notify
from .types import UserFollowNode, UserBlockingNode, SuspensionNode

STORAGE = FILE_STORAGE_CLASS()
THUMBNAIL_ALIASES = settings.THUMBNAIL_ALIASES
User = get_user_model()


class PatchUser(Output, DjangoPatchMutation):
    class Meta:
        model = User
        only_fields = [
            'display_name', 'country', 'birth_date', 'bio',
            'profile_picture', 'cover_photo', 'gender', 
            'is_active', 'is_premium', 'pinned_artist_post',
            'pinned_non_artist_post', 
        ]

    @classmethod
    def check_permissions(cls, root, info, input, id, obj: User):
        # Only current logged in user can update their account

        # The id used should be the pk not the global relay id NOPE. disambiguate_id exists xD
        # if not isinstance(id, int):
        #     raise GraphQLError(
        #         _("Use the primary key of the user which is an integer; relay ids are not supported"),
        #         extensions={'code': 'invalid'}
        #     ) 

        print(info.context.user, info.context.user.pk)
        print(obj, obj.pk)
        if info.context.user.pk == obj.pk:
            return 
        else:
            raise GraphQLError(
                _("You can not modify another user's account"),
                extensions={'code': 'not_owner'}
            )

    @classmethod
    @login_required
    def mutate(cls, root, info, input, id):
        # This method was overriden just to use the login_required decorator so as to have a 
        # consistent authentication api.
        return super().mutate(cls, root, info, input, id)


class UserLogout(Output, graphene.ClientIDMutation):

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        # TODO: to log a user out, the JWT cookie should be deleted on the 
        # client's browser and refresh tokens revoked.

        request = info.context
        print(request.COOKIES)
        # Since JWT is stateless(no record of authentication is saved), 
        # to log user out, we simply delete the JWT cookie
        try:
            del request.COOKIES['JWT']
        except KeyError:
            pass

        print(request.COOKIES)

        # Revoke refresh tokens
        revoke_user_refresh_token(request.user)

        return cls(success=False)


class ChangeUsername(Output, graphene.ClientIDMutation):
    """Change username of current logged in user(if they are permitted to change it)"""

    class Input:
        new_username = graphene.String()

    # The inherited class Output contains other appropriate return fields (success & errors)
    user = graphene.Field(UserNode)

    # The verification_required decorator from graphql_auth doesnt work here apparently,
    # so use custom permission verifier via user_passes_test.
    # Also, We use user_passes_test intead of login_required in the verify authenticated 
    # decorator to be able to provide a custom error message
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, new_username):
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

        # Revoke refresh tokens
        revoke_user_refresh_token(user)

        return cls(user=user)


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


class UpdateProfilePic(Output, graphene.ClientIDMutation):
    class Input:
        file = Upload(required=True)
    
    filename = graphene.String()
    base64_str = graphene.String()
    mimetype = graphene.String()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, file):
        # Validate file
        validate_profile_and_cover_photo(file)

        user = info.context.user

        # Get file extension and type to use with PIL
        file_extension, ftype = get_image_file_thumbnail_extension_and_type(file)

        # Create thumbnail of file
        image = Image.open(file)
        # image = image.convert('RGB')
        image.thumbnail(THUMBNAIL_ALIASES['']['profile_pic']['size'], Image.ANTIALIAS)
        thumb_file = BytesIO()
        image.save(thumb_file, format=ftype)
        
        use_filename = str(uuid.uuid4()) + '.' + file_extension
        mimetype = file.content_type
        file_bytes = thumb_file.getvalue()
        img_file = ContentFile(file_bytes)
        save_dir = get_post_media_upload_path(
            user.id,
            USERS_PROFILE_PICTURES_UPLOAD_DIR,
            use_filename
        )
        saved_filename = STORAGE.save(save_dir, img_file)
        thumb_file.close()

        # Update user's pfp
        user.profile_picture = saved_filename
        user.save(update_fields=[
            'profile_picture', 'profile_picture_width', 'profile_picture_height'
        ])

        return cls(
            filename=use_filename, 
            base64_str=base64.b64encode(file_bytes).decode('utf-8'), 
            mimetype=mimetype
        )


class UpdateCoverPhoto(Output, graphene.ClientIDMutation):
    class Input:
        file = Upload(required=True)
    
    filename = graphene.String()
    base64_str = graphene.String()
    mimetype = graphene.String()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, file):
        # Validate file
        validate_profile_and_cover_photo(file)

        user = info.context.user

        # Get file extension and type to use with PIL
        file_extension, ftype = get_image_file_thumbnail_extension_and_type(file)

        # Create thumbnail of file
        image = Image.open(file)
        # image = image.convert('RGB')
        image.thumbnail(THUMBNAIL_ALIASES['']['cover_photo']['size'], Image.ANTIALIAS)
        thumb_file = BytesIO()
        image.save(thumb_file, format=ftype)
        
        use_filename = str(uuid.uuid4()) + '.' + file_extension
        mimetype = file.content_type
        file_bytes = thumb_file.getvalue()
        img_file = ContentFile(file_bytes)
        save_dir = get_post_media_upload_path(
            user.id,
            USERS_COVER_PHOTOS_UPLOAD_DIR,
            use_filename
        )
        saved_filename = STORAGE.save(save_dir, img_file)
        thumb_file.close()

        # Update user's pfp
        user.cover_photo = saved_filename
        user.save(update_fields=[
            'cover_photo', 'cover_photo_width', 'cover_photo_height'
        ])

        return cls(
            filename=use_filename, 
            base64_str=base64.b64encode(file_bytes).decode('utf-8'), 
            mimetype=mimetype
        )


class FollowUser(Output, graphene.ClientIDMutation):
    class Input:
        user_id = graphene.ID(required=True)

    user_follow = graphene.Field(UserFollowNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, user_id):
        user, other_user_id = info.context.user, int(disambiguate_id(user_id))
        other_user = User.objects.get(id=other_user_id)
        follow_obj = user.follow_user(other_user)

        # Add action
        follow(user, other_user)

        return cls(user_follow=follow_obj)


class UnfollowUser(Output, graphene.ClientIDMutation):
    class Input:
        user_id = graphene.ID(required=True)

    follow_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, user_id):
        user, other_user_id = info.context.user, int(disambiguate_id(user_id))
        other_user = User.objects.get(id=other_user_id)
        deleted_obj_id = user.unfollow_user(other_user)

        # Remove activity
        unfollow(user, other_user)

        return cls(follow_id=deleted_obj_id)


class BlockUser(Output, graphene.ClientIDMutation):
    class Input:
        user_id = graphene.ID(required=True)

    user_block = graphene.Field(UserBlockingNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, user_id):
        user = info.context.user
        block_obj = user.block_user(int(disambiguate_id(user_id)))

        return cls(user_block=block_obj)


class UnblockUser(Output, graphene.ClientIDMutation):
    class Input:
        user_id = graphene.ID(required=True)

    block_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, user_id):
        user = info.context.user
        deleted_obj_id = user.unblock_user(int(disambiguate_id(user_id)))

        return cls(block_id=deleted_obj_id)


class DeactivateAccount(Output, graphene.ClientIDMutation):
    
    success = graphene.Boolean()
    account = graphene.Field(UserNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info):
        user = info.context.user
        user.deactivate()

        # Revoke refresh tokens
        revoke_user_refresh_token(user)

        # Refresh from db to get updated records
        user.refresh_from_db()
        return cls(account=user)


class ReactivateAccount(Output, graphene.ClientIDMutation):
 
    success = graphene.Boolean()
    account = graphene.Field(UserNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info):
        user = info.context.user
        user.reactivate()

        # Refresh from db to get updated records
        user.refresh_from_db()
        return cls(account=user)


class MarkUserVerified(Output, graphene.ClientIDMutation):
    class Input:
        user_id = graphene.ID(required=True)

    verified_user = graphene.Field(UserNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, user_id):
        # Only staff can mark user's account as verified
        user = info.context.user
        if not user.is_staff:
            raise GraphQLError(
                _("You can not mark a user's account as verified"),
                extensions={'code': 'not_permitted'}
            )

        target_user = User.objects.get(id=int(disambiguate_id(user_id)))
        target_user.type.is_verified = True
        target_user.type.save()
        target_user.verified_on = timezone.now()
        target_user.save(update_fields=['verified_on'])

        # Notify user
        notify.send(
            sender=User.site_services_account,  
            recipient=target_user, 
            verb=_("Your account has been successfully verified."),
            category=Notification.ACCOUNT
        )


class ToggleIsMod(Output, graphene.ClientIDMutation):
    class Input:
        user_id = graphene.ID(required=True)

    user = graphene.Field(UserNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, user_id):
        # Only staff can set or remove user moderator status
        user = info.context.user
        if not user.is_staff:
            raise GraphQLError(
                _("You can not change the moderator status of a user"),
                extensions={'code': 'not_permitted'}
            )

        target_user = User.objects.get(id=int(disambiguate_id(user_id)))
        is_now_mod = not target_user.is_mod
        target_user.type.is_mod = is_now_mod
        target_user.type.save()

        # Notify user
        if is_now_mod:
            notify.send(
                sender=User.site_services_account,  
                recipient=target_user, 
                verb=_(
                    "Congrats, you are now a moderator on this site. "
                    "Visit this link to learn more."
                ),
                category=Notification.ACCOUNT
            )
        else:
            # Should user be notified if he's no longer a mod?
            pass


class FlagUser(Output, graphene.ClientIDMutation):
    class Input:
        flag_user_id = graphene.ID(required=True)
        reason = FlagReason(required=True)

    flag_instance = graphene.Field(FlagInstanceNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, flag_user_id, reason):
        user = info.context.user

        # Only moderator can flag user account
        if not user.is_mod:
            raise GraphQLError(
                _("You can not flag a user's account"),
                extensions={'code': 'not_permitted'}
            )

        moderator = user
        user_to_flag = User.active_users.get(id=flag_user_id)
        flag_instance_obj = user.flag_object(user_to_flag, reason)

        # Notify all staff
        notify.send(
            sender=moderator,  
            recipient=User.staff, 
            verb=_("Please go through this user's account. Thanks"),
            target=user_to_flag,
            action_object=flag_instance_obj,
            category=Notification.REPORTED
        )

        return cls(flag_instance=flag_instance_obj)


class SuspendUser(Output, graphene.ClientIDMutation):
    class Input:
        suspend_user_id = graphene.ID(required=True)
        duration_in_days = graphene.Int()
        reason = graphene.String(required=True)

    suspension = graphene.Field(SuspensionNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        current_user = info.context.user
        suspend_user_id = int(disambiguate_id(input['suspend_user_id']))

        # Only staff can suspend users
        if not current_user.is_staff:
            raise GraphQLError(
                _("You are not permitted to suspend a user's account"),
                extensions={'code': 'not_permitted'}
            )

        suspension_obj = Suspension(
            suspender=current_user,
            suspended_user=User.active_users.get(id=suspend_user_id),
            reason=input['reason']
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


