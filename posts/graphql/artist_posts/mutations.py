import graphene
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from graphene_django_cud.mutations import DjangoCreateMutation, DjangoPatchMutation
from graphene_django_cud.util import disambiguate_id
from graphql import GraphQLError
from graphql_auth.bases import Output
from graphql_auth.decorators import login_required

from core.constants import FILE_STORAGE_CLASS
from flagging.graphql.types import *
from flagging.models.models import FlagInstance
from posts.constants import (
    COMMENT_CAN_EDIT_TIME_LIMIT, POST_CAN_EDIT_TIME_LIMIT, 
    FORM_AND_UPLOAD_DIR
)
from posts.models.artist_posts.models import (
    ArtistPost, ArtistPostComment, ArtistPostPhoto
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
        # If user can login(is_active), then his account status is verified;
        # thus no need to check whether user.status.verified is True
        login_required = True
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
        validate_comment(comment_body)
            
        return super().validate(root, info, input)

    @classmethod
    def mutate(cls, root, info, input):
        poster = info.context.user
        if cls._meta.login_required and not poster.is_authenticated:
            raise GraphQLError(_("Must be logged in to access this mutation."))

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

        # Save photos in cache(if any) to post
        save_dir = FORM_AND_UPLOAD_DIR['artist_post_photo']
        cache_key = f'{poster.username}-unposted-photos'
        user_photos_list = cache.get(cache_key, [])

        for photo_dict in user_photos_list:
            img_file = ContentFile(photo_dict['file_bytes'])
            saved_filename = STORAGE.save(save_dir + photo_dict['filename'], img_file)
            ArtistPostPhoto.objects.create(post=post, photo=saved_filename)

        # Save vidoes in cache if any
        # TODO
        # cache_key = f'{...}-unposted-video'
        # ...

        # Clear cache
        # TODO

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

        return_data = {cls._meta.return_field_name: post}
        return cls(**return_data)


class PatchArtistPost(Output, DjangoPatchMutation):
    class Meta:
        model = ArtistPost
        login_required = True
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
        

class DeleteArtistPost(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    post_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        post_id = disambiguate_id(input['post_id'])
        print(post_id)
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
        parent_post = ArtistPost.objects.get(id=disambiguate_id(input['parent_post_id']))

        # Create repost
        if repost_type == REPOST_TYPE.SIMPLE_REPOST:
            repost = ArtistPost.objects.create(
                is_simple_repost=True,
                body=body,
                poster=poster,
                parent=parent_post,
                artist=parent_post.artist
            )

        elif repost_type == REPOST_TYPE.NON_SIMPLE_REPOST:
            repost = ArtistPost.objects.create(
                is_simple_repost=False,
                body=body,
                poster=poster,
                parent=parent_post,
                artist=parent_post.artist
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
            
        return cls(repost=repost)


class PinArtistPost(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    pinned_post = graphene.Field(ArtistPostNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user, post_id = info.context.user, disambiguate_id(input['post_id'])
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
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        pinned_post = user.pinned_artist_post
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
    def mutate_and_get_payload(cls, root, info, **input):
        post_id, comment_id = disambiguate_id(input['post_id']), disambiguate_id(input['comment_id'])
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
    def mutate_and_get_payload(cls, root, info, **input):
        user, post_id = info.context.user, disambiguate_id(input['post_id'])
        post = ArtistPost.objects.get(id=post_id)

        # Post should belong to user
        if not post.poster_id == user.id:
            raise GraphQLError(
                _('You can only unpin a comment under your own post'),
                extensions={'code': 'not_permitted'}
            )

        pinned_comment = post.pinned_comment
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
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        download_obj = user.record_artist_post_download(disambiguate_id(input['post_id']))

        return cls(post_download=download_obj)


class BookmarkArtistPost(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    post_bookmark = graphene.Field(ArtistPostBookmarkNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        bookmark_obj = user.bookmark_artist_post(disambiguate_id(input['post_id']))

        return cls(post_bookmark=bookmark_obj)


class RemoveArtistPostBookmark(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    bookmark_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        post_id = disambiguate_id(input['post_id'])
        deleted_obj_id = info.context.user.remove_artist_post_bookmark(post_id)

        return cls(bookmark_id=deleted_obj_id)
    

class RateArtistPost(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)
        num_stars = RATING_STARS(required=True)

    post_rating = graphene.Field(ArtistPostRatingNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        created_obj = user.rate_artist_post(disambiguate_id(input['post_id']), input['num_stars'])

        return cls(post_rating=created_obj)


class RemoveArtistPostRating(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    rating_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        deleted_obj_id = user.remove_artist_post_rating(disambiguate_id(input['post_id']))

        return cls(rating_id=deleted_obj_id)


class CreateArtistPostAncestorComment(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)
        body = graphene.String(required=True)

    comment = graphene.Field(ArtistPostCommentNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        # Validate comment 
        comment_body = input['body']
        validate_comment(comment_body)

        user, post_id = info.context.user, disambiguate_id(input['post_id'])
        comment = ArtistPostComment.objects.create(
            post_concerned_id=post_id,
            body=comment_body,
            poster=user,
            num_child_comments=0
        )

        return cls(comment=comment)


class PatchArtistPostComment(DjangoPatchMutation):
    class Meta:
        model = ArtistPostComment
        login_required = True
        only_fields = ('body', )

    @classmethod
    def check_permissions(cls, root, info, input, id, obj: ArtistPostComment):
        """Only poster of post can edit the post and post should be editable"""

        # Only poster can edit post
        print(info.context.user)
        print(obj.poster)
        if info.context.user.id != obj.poster_id:
            raise GraphQLError(
                _("Only poster can edit post"),
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
    def mutate_and_get_payload(cls, root, info, **input):
        comment_id = disambiguate_id(input['comment_id'])
        deleted_obj_id = info.context.user.delete_artist_post_comment(comment_id)

        return cls(comment_id=deleted_obj_id)


class ReplyToArtistPostComment(Output, graphene.ClientIDMutation):
    class Input:
        parent_comment_id = graphene.ID(required=True)
        reply_body = graphene.String(required=True)

    reply = graphene.Field(ArtistPostCommentNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        # Validate comment 
        reply_body = input['reply_body']
        validate_comment(reply_body)

        user, parent_comment_id = info.context.user, disambiguate_id(input['parent_comment_id'])
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
        return cls(reply=reply)


class LikeArtistPostComment(Output, graphene.ClientIDMutation):
    class Input:
        comment_id = graphene.ID(required=True)

    comment_like = graphene.Field(ArtistPostCommentLikeNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        created_obj = user.add_artist_post_comment_like(disambiguate_id(input['comment_id']))

        return cls(comment_like=created_obj)


class RemoveArtistPostCommentLike(Output, graphene.ClientIDMutation):
    class Input:
        comment_id = graphene.ID(required=True)

    like_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        deleted_obj_id = user.remove_artist_post_comment_like(disambiguate_id(input['comment_id']))

        return cls(like_id=deleted_obj_id)


class FlagArtistPost(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)
        reason = graphene.Enum.from_enum(FlagInstance.FlagReason)

    flag_instance = graphene.Field(FlagInstanceNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user, post_id = info.context.user, disambiguate_id(input['post_id'])
        post = ArtistPost.objects.get(id=post_id)
        flag_instance_obj = user.flag_object(post, input['reason'])

        return cls(flag_instance=flag_instance_obj)


class UnflagArtistPost(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    flag_instance_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user, post_id = info.context.user, disambiguate_id(input['post_id'])
        post = ArtistPost.objects.get(id=post_id)
        deleted_obj_id = user.unflag_object(post)

        return cls(flag_instance_id=deleted_obj_id)


class FlagArtistPostComment(Output, graphene.ClientIDMutation):
    class Input:
        comment_id = graphene.ID(required=True)
        reason = graphene.Enum.from_enum(FlagInstance.FlagReason)

    flag_instance = graphene.Field(FlagInstanceNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user, comment_id = info.context.user, disambiguate_id(input['comment_id'])
        comment = ArtistPostComment.objects.get(id=comment_id)
        flag_instance_obj = user.flag_object(comment, input['reason'])

        return cls(flag_instance=flag_instance_obj)


class UnflagArtistPostComment(Output, graphene.ClientIDMutation):
    class Input:
        comment_id = graphene.ID(required=True)

    flag_instance_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user, comment_id = info.context.user, disambiguate_id(input['comment_id'])
        comment = ArtistPostComment.objects.get(id=comment_id)
        deleted_obj_id = user.unflag_object(comment)

        return cls(flag_instance_id=deleted_obj_id)


class AbsolveArtistPost(Output, graphene.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    flag = graphene.Field(FlagNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user, post_id = info.context.user, disambiguate_id(input['post_id'])
        
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
    def mutate_and_get_payload(cls, root, info, **input):
        user, comment_id = info.context.user, disambiguate_id(input['comment_id'])
        
        # Only moderator can absolve content
        if not user.is_mod:
            raise GraphQLError(
                _("Only moderators can absolve posts"),
                extensions={'code': 'not_permitted'}
            )

        comment = ArtistPostComment.objects.get(id=comment_id)
        user.absolve_object(comment)

        return cls(flag=comment.flag)


