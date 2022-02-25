import graphene
from actstream import action
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from graphene_django_cud.mutations import DjangoCreateMutation, DjangoPatchMutation
from graphene_django_cud.util import disambiguate_id
from graphql import GraphQLError
from graphql_auth.bases import Output
from graphql_auth.decorators import login_required

from core.constants import FILE_STORAGE_CLASS
from core.utils import get_user_cache_keys
from flagging.graphql.types import FlagNode, FlagInstanceNode, FlagReason
from notifications.models.models import Notification
from notifications.signals import notify
from posts.constants import (
    COMMENT_CAN_EDIT_TIME_LIMIT, POST_CAN_EDIT_TIME_LIMIT, 
    FORM_AND_UPLOAD_DIR
)
from posts.models.artist_posts.models import (
    ArtistPost, ArtistPostComment, ArtistPostPhoto, ArtistPostVideo
)
from ..common.types import REPOST_TYPE, RATING_STARS
from ..common.utils import validate_comment
from .types import (
    ArtistPostCommentNode, ArtistPostNode, ArtistPostBookmarkNode,
    ArtistPostCommentLikeNode, ArtistPostDownloadNode,
    ArtistPostRatingNode
)

STORAGE = FILE_STORAGE_CLASS()


class CreateArtistPost(Output, DjangoCreateMutation):
    class Meta:
        model = ArtistPost
        # If this attribute is edited, then also modify the mutate method.
        only_fields = ('body', 'is_private', 'artist', )
        custom_fields = {
            # If user creates post with a comment, then that comment is pinned by default.
            'pinned_comment_body': graphene.String(),
        }

    @classmethod
    def validate(cls, root, info, input):
        """
        Validate custom fields such as length of pinned_comment_body before moving
        to model fields
        """
        comment_body = input.get('pinned_comment_body', '')

        if comment_body:
            validate_comment(comment_body)
            
        return super().validate(root, info, input)

    @classmethod
    @login_required
    def mutate(cls, root, info, input):
        poster = info.context.user
        cls.check_permissions(root, info, input)
        cls.validate(root, info, input)

        # Create post
        post = ArtistPost(
            poster=poster,
            body=input['body'], 
            artist_id=cls.resolve_id(input['artist'])
        )
        if input.get('is_private') is True:
            post.is_private = True
        
        post.save()

        # Get user cache keys
        user_cache_keys = get_user_cache_keys(info.context.user.username)
        cache_photos_key, cache_video_key = user_cache_keys['photos'], user_cache_keys['video']

        # Save photos in cache(if any) to post
        save_dir = FORM_AND_UPLOAD_DIR['artist_post_photo']
        user_photos_list = cache.get(cache_photos_key, [])

        # Bulk create photos. Note that one of its caveats is that custom save method 
        # is not called; but since we have no custom save method, no worries then.
        post_photos = []
        for photo_dict in user_photos_list:
            img_file = ContentFile(photo_dict['file_bytes'])
            saved_filename = STORAGE.save(save_dir + photo_dict['filename'], img_file)
            post_photos.append(ArtistPostPhoto(post=post, photo=saved_filename))

        # If no photos were uploaded hence 'post_photos' is empty, there will be no prob
        ArtistPostPhoto.objects.bulk_create(post_photos)

        # Save videos that are in cache to post
		# TODO Call external api (aws elastic video encoder) to compress video

        video_dict = cache.get(cache_video_key, {})
        if video_dict:
            ArtistPostVideo.objects.create(
                post=post,
                video=video_dict['filepath'], 
                was_audio=video_dict['was_audio']
            )

        # Clear cache
        cache.delete(cache_photos_key)
        cache.delete(cache_video_key)

        # Save pinned comment in case it was also passed
        comment_body = input.get('pinned_comment_body', '')

        if comment_body:
            comment = ArtistPostComment.objects.create(
                body=comment_body, 
                poster=poster, 
                post_concerned=post
            )
            post.pinned_comment = comment
            post.save(update_fields=['pinned_comment'])

        # Update activity stream
        action.send(
            poster,
            verb=_('posted'),
            target=post,
        )

        # TODO Use google's natural language api to verify the level of "severity" or 
        # "sensitivity" of the post. Only share posts that have a given score i.e. don't share
        # posts with low score like "Polo G is trash"
        # https://cloud.google.com/natural-language/
        action.send(
            post.artist,
            verb=_('has new post'),
            target=post
        )

        return_data = {cls._meta.return_field_name: post}
        return cls(**return_data)


class PatchArtistPost(Output, DjangoPatchMutation):
    class Meta:
        model = ArtistPost
        only_fields = ('body', )

    @classmethod
    def check_permissions(cls, root, info, input, id, obj: ArtistPost):
        """Only poster of post can edit the post and post should be editable"""

        # Only poster can edit post
        print(info.context.user)
        print(obj.poster)
        if info.context.user.id != obj.poster_id:
            raise GraphQLError(
                _("Only poster can edit post"),
                extensions={'code': 'not_permitted'}
            )

        # Post should be editable
        if not obj.can_be_edited:
            err = _("You can no longer edit a post after %(can_edit_minutes)d minutes of its creation") \
                % {'can_edit_minutes': POST_CAN_EDIT_TIME_LIMIT.seconds // 60}

            raise GraphQLError(err, extensions={'code': 'not_editable'})

    @classmethod
    @login_required
    def mutate(cls, root, info, input, id):
        # This method was overriden just to use the login_required decorator so as to have a 
        # consistent authentication api.
        return super().mutate(cls, root, info, input, id)
        

class DeleteArtistPost(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    post_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, post_id):
        post_id = int(disambiguate_id(post_id))
        deleted_obj_id = info.context.user.delete_artist_post(post_id)

        # post_id will(should) always be equal to deleted_obj_id

        return cls(post_id=deleted_obj_id)
    

class RepostArtistPost(Output, graphene.ClientIDMutation):

    class Input:
        parent_post_id = graphene.ID(required=True)
        repost_type = REPOST_TYPE(required=True, default_value=REPOST_TYPE.SIMPLE_REPOST)
        body = graphene.String()
        # If user reposts with a comment, then that comment is pinned by default.
        pinned_comment_body = graphene.String()

    repost = graphene.Field(ArtistPostNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        # Validate comment length
        comment_body = input.get('pinned_comment_body', '')
        validate_comment(comment_body)

        body, repost_type = input['body'], input['repost_type']
        poster = info.context.user
        parent_post = ArtistPost.objects.get(id=int(disambiguate_id(input['parent_post_id'])))

        # Create repost
        if repost_type == REPOST_TYPE.SIMPLE_REPOST:
            repost = ArtistPost.objects.create(
                is_simple_repost=True,
                body=body,
                poster=poster,
                parent=parent_post,
                artist=parent_post.artist
            )

            action.send(
                poster,
                verb=_('shared'),  # Poster reposted post (poster shared post)
                target=parent_post,
                action_object=repost
            )

        elif repost_type == REPOST_TYPE.NON_SIMPLE_REPOST:
            repost = ArtistPost.objects.create(
                is_simple_repost=False,
                body=body,
                poster=poster,
                parent=parent_post,
                artist=parent_post.artist
            )

            action.send(
                poster,
                verb=_('reposted'), 
                target=parent_post,
                action_object=repost
            )

            # TODO add media in cache to post

        # Save pinned comment in case it was also passed
        if comment_body:
            comment = ArtistPostComment.objects.create(
                body=comment_body, 
                poster=poster, 
                post_concerned=repost
            )
            repost.pinned_comment = comment
            repost.save(update_fields=['pinned_comment'])
        
        # Notify parent post owner 
        notify.send(
            sender=poster,  
            recipient=parent_post.poster, 
            verb=_("reposted"),
            target=parent_post,
            action_object=repost,
            category=Notification.REPOST
        )
            
        return cls(repost=repost)


class PinArtistPost(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    pinned_post = graphene.Field(ArtistPostNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, post_id):
        user, post_id = info.context.user, int(disambiguate_id(post_id))
        post = ArtistPost.objects.get(id=post_id)

        # Post should belong to user
        if post.poster_id != user.id:
            raise GraphQLError(
                _('You can only pin your own post'),
                extensions={'code': 'not_permitted'}
            )

        user.pinned_artist_post = post
        user.save(update_fields=['pinned_artist_post'])

        return cls(pinned_post=post)


class UnpinPinnedArtistPost(Output, graphene.ClientIDMutation):
    
    unpinned_post = graphene.Field(ArtistPostNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info):
        user = info.context.user
        pinned_post = user.pinned_artist_post

        if pinned_post:
            user.pinned_artist_post = None
            user.save(update_fields=['pinned_artist_post'])

        return cls(unpinned_post=pinned_post)


class PinArtistPostComment(Output, graphene.ClientIDMutation):
    class Input:
        comment_id = graphene.ID(required=True)
        post_id = graphene.ID(required=True)

    pinned_comment = graphene.Field(ArtistPostCommentNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, comment_id, post_id):
        post_id, comment_id = int(disambiguate_id(post_id)), int(disambiguate_id(comment_id))
        comment = ArtistPostComment.objects.get(id=comment_id)

        # Comment should be of post
        if comment.post_concerned_id != post_id:
            raise GraphQLError(
                _('This comment does not belong to this post'),
                extensions={'code': 'not_child_comment'}
            )

        # Comment should be ancestor
        if not comment.is_ancestor:
            raise GraphQLError(
                _('You can only pin an ancestor comment'),
                extensions={'code': 'invalid'}
            )

        user, post = info.context.user, ArtistPost.objects.get(id=post_id)
        # Post should belong to user
        if post.poster_id != user.id:
            raise GraphQLError(
                _('You can only pin a comment under your own post'),
                extensions={'code': 'not_permitted'}
            )

        post.pinned_comment = comment
        post.save(update_fields=['pinned_comment'])


class UnpinPinnedArtistPostComment(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)
    
    unpinned_comment = graphene.Field(ArtistPostCommentNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, post_id):
        user, post_id = info.context.user, int(disambiguate_id(post_id))
        post = ArtistPost.objects.get(id=post_id)

        # Post should belong to user
        if not post.poster_id == user.id:
            raise GraphQLError(
                _('You can only unpin a comment under your own post'),
                extensions={'code': 'not_permitted'}
            )

        pinned_comment = post.pinned_comment

        if pinned_comment:
            post.pinned_comment = None
            post.save(update_fields=['pinned_comment'])

        return cls(unpinned_comment=pinned_comment)


# I can't use django-cud's create mutation because apparently it has
# a problem when the db_column is set using a name other than the {field_name}_id
class RecordArtistPostDownload(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    post_download = graphene.Field(ArtistPostDownloadNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, post_id):
        user = info.context.user
        download_obj = user.record_artist_post_download(int(disambiguate_id(post_id)))

        return cls(post_download=download_obj)


class BookmarkArtistPost(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    post_bookmark = graphene.Field(ArtistPostBookmarkNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, post_id):
        user = info.context.user
        bookmark_obj = user.bookmark_artist_post(int(disambiguate_id(post_id)))

        return cls(post_bookmark=bookmark_obj)


class RemoveArtistPostBookmark(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    bookmark_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, post_id):
        post_id = int(disambiguate_id(post_id))
        deleted_obj_id = info.context.user.remove_artist_post_bookmark(post_id)

        return cls(bookmark_id=deleted_obj_id)
    

class RateArtistPost(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)
        num_stars = RATING_STARS(required=True)

    post_rating = graphene.Field(ArtistPostRatingNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, post_id, num_stars):
        user, post_id = info.context.user, int(disambiguate_id(post_id))
        post = ArtistPost.objects.get(id=post_id)
        poster = post.poster
        rating_obj = user.rate_artist_post(post, num_stars)

        # Notify poster of post
        notify.send(
            sender=user,
            recipient=poster, 
            verb=_("rated your post"),
            target=post,
            action_object=rating_obj,
            category=Notification.RATING
        )

        # Add this to activity stream if rating has 3 or 5 stars
        if num_stars == RATING_STARS.THREE or num_stars == RATING_STARS.FIVE:
            action.send(
                user,
                verb=_('rated'),  
                target=post,
                action_object=rating_obj
            )

        return cls(post_rating=rating_obj)


class RemoveArtistPostRating(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    rating_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, post_id):
        user = info.context.user
        deleted_obj_id = user.remove_artist_post_rating(int(disambiguate_id(post_id)))

        return cls(rating_id=deleted_obj_id)


class CreateArtistPostAncestorComment(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)
        body = graphene.String(required=True)

    comment = graphene.Field(ArtistPostCommentNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, post_id, body):
        # Validate comment 
        comment_body = body
        validate_comment(comment_body)

        user, post_id = info.context.user, int(disambiguate_id(post_id))
        post = ArtistPost.objects.get(id=post_id)
        comment = ArtistPostComment.objects.create(
            post_concerned_id=post,
            body=comment_body,
            poster=user,
            num_child_comments=0
        )

        # Notify poster of post
        notify.send(
            sender=user,
            recipient=post.poster, 
            verb=_("commented on"),
            target=post,
            category=Notification.COMMENT
        )

        # Send action
        action.send(
            user,
            verb='commented on',
            target=post,
            action_object=comment
        )

        return cls(comment=comment)


class PatchArtistPostComment(Output, DjangoPatchMutation):
    class Meta:
        model = ArtistPostComment
        login_required = True
        only_fields = ('body', )

    @classmethod
    def check_permissions(cls, root, info, input, id, obj: ArtistPostComment):
        """Only poster of comment can edit the comment and comment should be editable"""

        # Only poster can edit comment
        print(info.context.user)
        print(obj.poster)
        if info.context.user.id != obj.poster_id:
            raise GraphQLError(
                _("Only poster can edit comment"),
                extensions={'code': 'not_permitted'}
            )

        # Comment should be editable
        if not obj.can_be_edited:
            err = _("You can no longer edit a comment after %(can_edit_minutes)d minutes of its creation") \
                % {'can_edit_minutes': COMMENT_CAN_EDIT_TIME_LIMIT.seconds // 60}

            raise GraphQLError(err, extensions={'code': 'not_editable'})


class DeleteArtistPostComment(Output, graphene.ClientIDMutation):
    class Input:
        comment_id = graphene.ID(required=True)

    comment_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, comment_id):
        comment_id = int(disambiguate_id(comment_id))
        deleted_obj_id = info.context.user.delete_artist_post_comment(comment_id)

        return cls(comment_id=deleted_obj_id)


class ReplyToArtistPostComment(Output, graphene.ClientIDMutation):
    class Input:
        parent_comment_id = graphene.ID(required=True)
        reply_body = graphene.String(required=True)

    reply = graphene.Field(ArtistPostCommentNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, parent_comment_id, reply_body):
        # Validate comment 
        validate_comment(reply_body)

        user, parent_comment_id = info.context.user, int(disambiguate_id(parent_comment_id))
        parent_comment = ArtistPostComment.objects.get(id=parent_comment_id)

        reply = ArtistPostComment(
            parent=parent_comment,
            post_concerned_id=parent_comment.post_concerned_id,
            body=reply_body,
            poster=user
        )

        # If parent comment is ancestor, set ancestor to parent comment 
        if parent_comment.is_ancestor:
            reply.ancestor = parent_comment
        else:
            reply.ancestor_id = parent_comment.ancestor_id
        
        reply.save()

        # Apparently we need to do this, i guess to reload objects from the database.
        # I thing this issue arose because be didn't use the create method, but rather
        # instantiated the class before calling save().
        reply.refresh_from_db()

        # Notify poster of parent comment
        notify.send(
            sender=user,
            recipient=parent_comment.poster, 
            verb=_("replied to your comment"),
            target=parent_comment,
            action_object=reply,
            category=Notification.COMMENT_REPLY
        )

        return cls(reply=reply)


class LikeArtistPostComment(Output, graphene.ClientIDMutation):
    class Input:
        comment_id = graphene.ID(required=True)

    comment_like = graphene.Field(ArtistPostCommentLikeNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, comment_id):
        user, comment_id = info.context.user, int(disambiguate_id(comment_id))
        comment = ArtistPostComment.objects.get()
        like_obj = user.add_artist_post_comment_like(comment)

        # Notify poster of comment
        notify.send(
            sender=user,
            recipient=comment.poster, 
            verb=_("liked your coment"),
            target=comment,
            action_object=like_obj,
            category=Notification.COMMENT_LIKE
        )

        return cls(comment_like=like_obj)


class RemoveArtistPostCommentLike(Output, graphene.ClientIDMutation):
    class Input:
        comment_id = graphene.ID(required=True)

    like_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, comment_id):
        user = info.context.user
        deleted_obj_id = user.remove_artist_post_comment_like(int(disambiguate_id(comment_id)))

        return cls(like_id=deleted_obj_id)


class FlagArtistPost(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)
        reason = FlagReason(required=True)

    flag_instance = graphene.Field(FlagInstanceNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, post_id, reason):
        user, post_id = info.context.user, int(disambiguate_id(post_id))
        post = ArtistPost.objects.get(id=post_id)
        flag_instance_obj = user.flag_object(post, reason)

        return cls(flag_instance=flag_instance_obj)


class UnflagArtistPost(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    flag_instance_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, post_id):
        user, post_id = info.context.user, int(disambiguate_id(post_id))
        post = ArtistPost.objects.get(id=post_id)
        deleted_obj_id = user.unflag_object(post)

        return cls(flag_instance_id=deleted_obj_id)


class FlagArtistPostComment(Output, graphene.ClientIDMutation):
    class Input:
        comment_id = graphene.ID(required=True)
        reason = FlagReason(required=True)

    flag_instance = graphene.Field(FlagInstanceNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, comment_id, reason):
        user, comment_id = info.context.user, int(disambiguate_id(comment_id))
        comment = ArtistPostComment.objects.get(id=comment_id)
        flag_instance_obj = user.flag_object(comment, reason)

        return cls(flag_instance=flag_instance_obj)


class UnflagArtistPostComment(Output, graphene.ClientIDMutation):
    class Input:
        comment_id = graphene.ID(required=True)

    flag_instance_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, comment_id):
        user, comment_id = info.context.user, int(disambiguate_id(comment_id))
        comment = ArtistPostComment.objects.get(id=comment_id)
        deleted_obj_id = user.unflag_object(comment)

        return cls(flag_instance_id=deleted_obj_id)


class AbsolveArtistPost(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    flag = graphene.Field(FlagNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, post_id):
        user, post_id = info.context.user, int(disambiguate_id(post_id))
        
        # Only moderator can absolve content
        if not user.is_mod:
            raise GraphQLError(
                _("Only moderators can absolve posts"),
                extensions={'code': 'not_permitted'}
            )

        post = ArtistPost.objects.get(id=post_id)
        user.absolve_object(post)

        return cls(flag=post.flag)


class AbsolveArtistPostComment(Output, graphene.ClientIDMutation):
    class Input:
        comment_id = graphene.ID(required=True)

    flag = graphene.Field(FlagNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, comment_id):
        user, comment_id = info.context.user, int(disambiguate_id(comment_id))
        
        # Only moderator can absolve content
        if not user.is_mod:
            raise GraphQLError(
                _("Only moderators can absolve posts"),
                extensions={'code': 'not_permitted'}
            )

        comment = ArtistPostComment.objects.get(id=comment_id)
        user.absolve_object(comment)

        return cls(flag=comment.flag)


class DeleteFlaggedArtistPost(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    post_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, post_id):
        user, post_id = info.context.user, int(disambiguate_id(post_id))

        # Only moderator can delete content
        if not user.is_mod:
            raise GraphQLError(
                _("Only moderators can absolve posts"),
                extensions={'code': 'not_permitted'}
            )

        # Post should be flagged before moderator can delete it
        post = ArtistPost.objects.get(id=post_id)
        if not post.is_flagged:
            raise GraphQLError(
                _("Moderators can only delete flagged posts"),
                extensions={'code': 'not_permitted'}
            )
        
        poster = post.poster
        deleted_obj_id = user.delete_artist_post(post)

        # Notify poster of post
        notify.send(
            sender=poster,  # just use same user as sender
            recipient=poster, 
            verb=_(
                "One of your posts has been deleted because it was considered "
                "inappropriate. Please try to not post such content in the future. Thanks"
            ),
            category=Notification.FLAGGED_CONTENT_DELETED
        )

        return cls(post_id=deleted_obj_id)


class DeleteFlaggedArtistPostComment(Output, graphene.ClientIDMutation):
    class Input:
        comment_id = graphene.ID(required=True)

    comment_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, comment_id):
        user, comment_id = info.context.user, int(disambiguate_id(comment_id))

        # Only moderator can delete content
        if not user.is_mod:
            raise GraphQLError(
                _("Only moderators can absolve posts"),
                extensions={'code': 'not_permitted'}
            )

        # comment should be flagged before moderator can delete it
        comment = ArtistPostComment.objects.get(id=comment_id)
        if not comment.is_flagged:
            raise GraphQLError(
                _("Moderators can only delete flagged posts"),
                extensions={'code': 'not_permitted'}
            )
        
        poster = comment.poster
        deleted_obj_id = user.delete_artist_post_comment(comment)

        # Notify poster of comment
        notify.send(
            sender=poster,  # just use same user as sender
            recipient=poster, 
            verb=_(
                "One of your comments has been deleted because it was considered "
                "inappropriate. Please try to not post such content in the future. Thanks"
            ),
            category=Notification.FLAGGED_CONTENT_DELETED
        )

        return cls(comment_id=deleted_obj_id)

