import graphene
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from graphene_django_cud.mutations import (
    DjangoCreateMutation, DjangoPatchMutation,
    DjangoDeleteMutation,
)
from graphene_django_cud.util import disambiguate_id
from graphql import GraphQLError
from graphql_auth.decorators import login_required

from core.constants import FILE_STORAGE_CLASS
from posts.constants import POST_CAN_EDIT_TIME_LIMIT, FORM_AND_UPLOAD_DIR
from posts.models.artist_posts.models import (
    ArtistPost, ArtistPostComment, ArtistPostPhoto
)
# Import types
from ..common.types import *
from ..common.utils import validate_comment
from .types import *

STORAGE = FILE_STORAGE_CLASS()


class CreateArtistPostMutation(DjangoCreateMutation):
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


class PatchArtistPostMutation(DjangoPatchMutation):
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
        

class DeleteArtistPostMutation(graphene.relay.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    deleted = graphene.Boolean()
    post_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        post_id = disambiguate_id(input['post_id'])
        deleted_obj_id = info.context.user.delete_artist_post(post_id)

        # post_id will(should) always be equal to deleted_obj_id

        return DeleteArtistPostMutation(deleted=True, post_id=deleted_obj_id)
    

class RepostArtistPostMutation(graphene.relay.ClientIDMutation):

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
            
        return RepostArtistPostMutation(repost=repost)


# I can't use django-cud's create mutation because apparently it has
# a problem when the db_column is set using a name other than the {field_name}_id
class RecordArtistPostDownloadMutation(graphene.relay.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    post_download = graphene.Field(ArtistPostDownloadNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        download_obj = user.record_artist_post_download(disambiguate_id(input['post_id']))

        return RecordArtistPostDownloadMutation(post_download=download_obj)


class BookmarkArtistPostMutation(graphene.relay.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    post_bookmark = graphene.Field(ArtistPostBookmarkNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        bookmark_obj = user.bookmark_artist_post(disambiguate_id(input['post_id']))

        return BookmarkArtistPostMutation(post_bookmark=bookmark_obj)


class DeleteArtistPostBookmarkMutation(graphene.relay.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    deleted = graphene.Boolean()
    bookmark_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        post_id = disambiguate_id(input['post_id'])
        deleted_obj_id = info.context.user.remove_artist_post_bookmark(post_id)

        return DeleteArtistPostMutation(deleted=True, bookmark_id=deleted_obj_id)
    

class RateArtistPostMutation(graphene.relay.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)
        num_stars = RATING_STARS(required=True)

    post_rating = graphene.Field(ArtistPostRatingNode)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        created_obj = user.rate_artist_post(disambiguate_id(input['post_id']), input['num_stars'])

        return RateArtistPostMutation(post_rating=created_obj)


class DeleteArtistPostRatingMutation(graphene.relay.ClientIDMutation):
    class Input:
        post_id = graphene.ID(required=True)

    deleted = graphene.Boolean()
    rating_id = graphene.Int()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        deleted_obj_id = user.remove_artist_post_rating(disambiguate_id(input['post_id']))

        return DeleteArtistPostMutation(deleted=True, rating_id=deleted_obj_id)


