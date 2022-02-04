import graphene
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from graphene_django_cud.mutations import (
    DjangoCreateMutation, DjangoPatchMutation,
    DjangoDeleteMutation,
)
from graphene_django_cud.util import disambiguate_id
from graphql import GraphQLError
from graphql_auth.decorators import login_required

from posts.constants import MAX_COMMENT_LENGTH, POST_CAN_EDIT_TIME_LIMIT
from posts.models.artist_posts.models import (
    ArtistPost, ArtistPostComment, 
)
# Import types
from .types import *


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
        if len(comment_body) > MAX_COMMENT_LENGTH:
            raise ValidationError(
				_('Comments should be less than %(max_length)s characters'),
				code='max_length',
				params={'max_length': MAX_COMMENT_LENGTH}
			)
            
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
        

class DeleteArtistPostMutation(DjangoDeleteMutation):
    class Meta:
        model = ArtistPost    
        
    @classmethod
    def check_permissions(cls, root, info, id, obj: ArtistPost):
        """
        Only poster or staff can delete post, moderator can also delete post if it's flagged
        """
        user = info.context.user

        if user.is_staff or user.id == obj.poster_id:
            return

        if user.is_mod and obj.is_flagged:
            return 

        raise GraphQLError("Not permitted to access this mutation.")    
    

# class RepostArtistPostMutation(graphene.relay.ClientIDMutation):

#     class Input:
#         post_id = graphene.ID(required=True)
#         comment = graphene.String(required=False)

#     repost = graphene.Field(ArtistPostRepostNode)

#     @classmethod
#     @login_required
#     def mutate_and_get_payload(cls, root, info, **input):
#         repost = ArtistPostRepost.objects.create(
#             comment=input.get('comment', ''),
#             post_id=disambiguate_id(input['post_id']),
#             reposter=info.context.user
#         )

#         return RepostArtistPostMutation(repost=repost)

