"""Contains operations for the various models as mixins"""

from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db.models import F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.constants import USERNAME_CHANGE_WAIT_PERIOD
from accounts.models.artists.models import ArtistFollow
from accounts.utils import get_user, get_artist
from flagging.models.models import Flag, FlagInstance
from notifications.models.models import Notification
from notifications.signals import notify
from posts.models.artist_posts.models import (
    ArtistPostBookmark, ArtistPostCommentLike, 
    ArtistPostDownload, ArtistPostRating, ArtistPost
)
from posts.models.non_artist_posts.models import (
    NonArtistPostBookmark, NonArtistPostCommentLike, 
    NonArtistPostDownload, NonArtistPostRating, NonArtistPost
)
from posts.utils import (
    get_artist_post, get_artist_post_comment,
    get_non_artist_post, get_non_artist_post_comment
)


class UserOperations:
    """Mixin containing operations to be used on the User model"""

    # Copied from django's AbstractUser model
    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Send an email to this user. If `from_email` is None, DEFAULT_FROM_EMAIL
        defined in the settings file will be used.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def deactivate(self):
        """Mark user as inactive but allow his record in database."""
        # Don't actually delete user account, just do this instead
        self.deactivated_on = timezone.now()
        self.is_active = False
        self.save(update_fields=['is_active', 'deactivated_on'])

        # Update graphql_auth status
        self.status.verified = False
        self.status.save(update_fields=['verified'])

    def reactivate(self):
        # TODO conditions/caveats for account reactivation
        self.deactivated_on = None
        self.is_active = True
        self.save(update_fields=['is_active', 'deactivated_on'])

        # Update graphql_auth status
        self.status.verified = True
        self.status.save(update_fields=['verified'])

    def change_username(self, new_username: str):
        """
        Change a user's username. This method should be used to modify
        a user's username rather than directly calling save().
        """
        if not self.can_change_username:
            raise ValidationError(
                _(
                    "You cannot change your username until the %(can_change_date)s; "
                    "you need to wait %(wait_period)s days after changing your username."
                ),
                code="can't_change_username_yet",
                params={
                    'can_change_date': str(self.can_change_username_until_date),
                    'wait_period': USERNAME_CHANGE_WAIT_PERIOD
                }
            )

        if self.username == new_username:
            raise ValidationError(
                _("This is your current username"),
                code="same_username"
            )

        self.username = new_username
        self.last_changed_username_on = timezone.now()
        self.save(update_fields=['username', 'last_changed_username_on'])

    def has_downloaded_post(self, post):
        """Return whether user has downloaded `post` or not"""

        if isinstance(post, ArtistPost):
            return ArtistPostDownload.objects.filter(
                downloader=self,
                post=post
            ).exists()
        elif isinstance(post, NonArtistPost):
            return NonArtistPostDownload.objects.filter(
                downloader=self,
                post=post
            ).exists()
        else:
            raise TypeError(_('Object should be instance of ArtstPost or NonArtistPost'))

    def can_download_post(self, post):
        """
        Returns whether user can download `post`. 
        Note that if a user is permitted to download an already downloaded post 
        unlimited times.
        """
        if self.has_downloaded_post(post):
            return True

        return self.can_download

    def num_downloads(self, month: int, year: int):
        """
        Get the number of posts the user downloaded in the `month` month of the year `year`.
        """
        return ArtistPostDownload.objects.filter(
            downloader=self,
            downloaded_on__month=month,
            downloaded_on__year=year
        ).count() + NonArtistPostDownload.objects.filter(
            downloader=self,
            downloaded_on__month=month,
            downloaded_on__year=year
        ).count()

    def flag_object(self, obj, reason):
        """`reason` has to be a valid reason in FlagInstance.FLAG_REASONS"""
        return FlagInstance.objects.create_flag(self, obj.flag, reason)['flag_instance']

    def unflag_object(self, obj):
        return FlagInstance.objects.delete_flag(self, obj.flag)['flag_instance_id']

    def absolve_object(self, obj):
        """
        Resolve the flag of an object. This object should use the FlagMixin.
        User should be a moderator.
        """
        if not self.is_mod:
            raise ValidationError(
                _('Only moderators can absolve content'),
                code="can't_absolve_content"
            )

        flag = obj.flag
        flag.toggle_state(Flag.State.RESOLVED, self)

    def follow_artist(self, artist_or_id):
        artist = get_artist(artist_or_id)
        follow_obj = ArtistFollow.objects.create(follower=self, artist=artist)

        artist.num_followers = F('num_followers') + 1
        artist.save(update_fields=['num_followers'])

        return follow_obj

    def unfollow_artist(self, artist_or_id):
        artist = get_artist(artist_or_id)
        follow_obj = ArtistFollow.objects.get(follower=self, artist=artist)
        follow_obj_id = follow_obj.id
        follow_obj.delete()

        artist.num_followers = F('num_followers') - 1
        artist.save(update_fields=['num_followers'])

        return follow_obj_id

    def follow_user(self, other_or_id):
        from accounts.models.users.models import UserFollow

        other = get_user(other_or_id)
        if self.has_blocked_user(other):
            raise ValidationError(
                _("You can't follow a user that you've blocked")
            )

        follow_obj = UserFollow.objects.create(follower=self, followed=other)

        self.num_following = F('num_following') + 1
        self.save(update_fields=['num_following'])

        other.num_followers = F('num_followers') + 1
        other.save(update_fields=['num_followers'])

        # Notify followed user (self followed other)
        notify.send(
            sender=self,  
            recipient=other, 
            verb=_("followed you"),
            action_object=follow_obj,
            category=Notification.FOLLOW
        )

        return follow_obj

    def unfollow_user(self, other_or_id):
        from accounts.models.users.models import UserFollow

        other = get_user(other_or_id)

        follow_obj = UserFollow.objects.get(follower=self, followed=other)
        follow_obj_id = follow_obj.id
        follow_obj.delete()

        self.num_following = F('num_following') - 1
        self.save(update_fields=['num_following'])

        other.num_followers = F('num_followers') - 1
        other.save(update_fields=['num_followers'])

        return follow_obj_id

    def is_following_user(self, other_or_id):
        other = get_user(other_or_id)
        return self in other.followers.all()

    def is_following_artist(self, artist_or_id):
        artist = get_artist(artist_or_id)
        return self in artist.followers.all()
    
    def block_user(self, other_or_id):
        from accounts.models.users.models import UserBlocking

        other = get_user(other_or_id)
        block_obj = UserBlocking.objects.create(blocker=self, blocked=other)

        # Unfollow user if user is following user
        if other in self.following.all():
            self.unfollow_user(other)

        return block_obj

    def unblock_user(self, other_or_id):
        from accounts.models.users.models import UserBlocking

        other = get_user(other_or_id)
        block_obj = UserBlocking.objects.get(blocker=self, blocked=other)
        block_obj_id = block_obj.id
        block_obj.delete()

        return block_obj_id

    def has_blocked_user(self, other_or_id):
        """Return `True` if self has blocked other else `False`"""
        other = get_user(other_or_id)
        return other in self.blocked_users.all()

    # For creating posts and comments, call the corresponding models directly. 
    # Appropriate signals have been attached

    def delete_artist_post(self, post_or_id):
        post = get_artist_post(post_or_id)

        # Ensure user is permitted to delete post
        if not (self.id == post.poster_id or self.is_staff or (self.is_mod and post.is_flagged)):
            raise ValidationError(
                _('Not permitted to delete this post.'),
                code='not_permitted'
            )

        post_id = post.id
        poster = post.poster
        post.delete()

        if post.is_parent:
            # Decrement user's post count
            poster.num_artist_posts = F('num_artist_posts') - 1
            poster.save(update_fields=['num_artist_posts'])
        else:
            parent_post = post.parent
            poster.num_artist_post_reposts = F('num_artist_post_reposts') - 1
            poster.save(update_fields=['num_artist_post_reposts'])

            if post.is_simple_repost:
                parent_post.num_simple_reposts = F('num_simple_reposts') - 1
                parent_post.save(update_fields=['num_simple_reposts'])

            else:
                parent_post.num_non_simple_reposts = F('num_non_simple_reposts') - 1
                parent_post.save(update_fields=['num_non_simple_reposts'])

        return post_id

    def delete_non_artist_post(self, post_or_id):
        post = get_non_artist_post(post_or_id)

        # Ensure user is permitted to delete post
        if not (self.id == post.poster_id or self.is_staff or (self.is_mod and post.is_flagged)):
            raise ValidationError(
                _('Not permitted to delete this post.'),
                code='not_permitted'
            )

        post_id = post.id
        poster = post.poster
        post.delete()

        if post.is_parent:
            # Decrement user's post count
            poster.num_non_artist_posts = F('num_non_artist_posts') - 1
            poster.save(update_fields=['num_non_artist_posts'])
        else:
            parent_post = post.parent
            poster.num_non_artist_post_reposts = F('num_non_artist_post_reposts') - 1
            poster.save(update_fields=['num_non_artist_post_reposts'])

            if post.is_simple_repost:
                parent_post.num_simple_reposts = F('num_simple_reposts') - 1
                parent_post.save(update_fields=['num_simple_reposts'])

            else:
                parent_post.num_non_simple_reposts = F('num_non_simple_reposts') - 1
                parent_post.save(update_fields=['num_non_simple_reposts'])

        return post_id

    def delete_artist_post_comment(self, comment_or_id):
        comment = get_artist_post_comment(comment_or_id)

        # Ensure user is permitted to delete post
        if not (self.id == comment.poster_id or self.is_staff or (self.is_mod and comment.is_flagged)):
            raise ValidationError(
                _('Not permitted to delete this comment.'),
                code='not_permitted'
            )

        comment_id = comment.id
        parent = comment.parent
        ancestor, poster, post = comment.ancestor, comment.poster, comment.post_concerned
        comment.delete()

        # Update parent comment's number of replies
        if parent:
            parent.num_replies = F('num_replies') - 1
            parent.save(update_fields=['num_replies'])

        # If we are deleting an ancestor comment
        if comment.is_ancestor:
            post.num_ancestor_comments = F('num_ancestor_comments') - 1
            post.save(update_fields=['num_ancestor_comments'])

            poster.num_ancestor_artist_post_comments = F('num_ancestor_artist_post_comments') - 1
            poster.save(update_fields=['num_ancestor_artist_post_comments'])
        else:
            ancestor.num_child_comments = F('num_child_comments') - 1
            ancestor.save(update_fields=['num_child_comments'])

        return comment_id

    def delete_non_artist_post_comment(self, comment_or_id):
        comment = get_non_artist_post_comment(comment_or_id)

        # Ensure user is permitted to delete post
        if not (self.id == comment.poster_id or self.is_staff or (self.is_mod and comment.is_flagged)):
            raise ValidationError(
                _('Not permitted to delete this comment.'),
                code='not_permitted'
            )

        comment_id = comment.id
        parent = comment.parent
        ancestor, poster, post = comment.ancestor, comment.poster, comment.post_concerned
        comment.delete()

        # Update parent comment's number of replies
        if parent:
            parent.num_replies = F('num_replies') - 1
            parent.save(update_fields=['num_replies'])

        # If we are deleting an ancestor comment
        if comment.is_ancestor:
            post.num_ancestor_comments = F('num_ancestor_comments') - 1
            post.save(update_fields=['num_ancestor_comments'])

            poster.num_ancestor_artist_post_comments = F('num_ancestor_artist_post_comments') - 1
            poster.save(update_fields=['num_ancestor_artist_post_comments'])
        else:
            ancestor.num_child_comments = F('num_child_comments') - 1
            ancestor.save(update_fields=['num_child_comments'])

        return comment_id

    def add_artist_post_comment_like(self, comment_or_id):
        comment = get_artist_post_comment(comment_or_id)

        like_obj = ArtistPostCommentLike.objects.create(
            comment=comment,
            liker=self,
        )
        comment.num_likes = F('num_likes') + 1
        comment.save(update_fields=['num_likes'])

        return like_obj

    def add_non_artist_post_comment_like(self, comment_or_id):
        comment = get_non_artist_post_comment(comment_or_id)

        like_obj = NonArtistPostCommentLike.objects.create(
            comment=comment,
            liker=self,
        )
        comment.num_likes = F('num_likes') + 1
        comment.save(update_fields=['num_likes'])

        return like_obj

    def remove_artist_post_comment_like(self, comment_or_id):
        comment = get_artist_post_comment(comment_or_id)
        like_obj = ArtistPostCommentLike.objects.get(liker=self, comment=comment)
        like_obj_id = like_obj.id
        like_obj.delete()

        comment.num_likes = F('num_likes') - 1
        comment.save(update_fields=['num_likes'])
        return like_obj_id

    def remove_non_artist_post_comment_like(self, comment_or_id):
        comment = get_non_artist_post_comment(comment_or_id)
        like_obj = NonArtistPostCommentLike.objects.get(liker=self, comment=comment)
        like_obj_id = like_obj.id
        like_obj.delete()

        comment.num_likes = F('num_likes') - 1
        comment.save(update_fields=['num_likes'])
        return like_obj_id

    def rate_artist_post(self, post_or_id, num_stars):
        post = get_artist_post(post_or_id)
        rating_obj = ArtistPostRating.objects.create(post=post, rater=self, num_stars=num_stars)

        post.num_stars = F('num_stars') + num_stars
        post.save(update_fields=['num_stars']) 

        return rating_obj

    def rate_non_artist_post(self, post_or_id, num_stars):
        post = get_non_artist_post(post_or_id)
        rating_obj = NonArtistPostRating.objects.create(post=post, rater=self, num_stars=num_stars)

        post.num_stars = F('num_stars') + num_stars
        post.save(update_fields=['num_stars']) 

        return rating_obj

    def remove_artist_post_rating(self, post_or_id):
        post = get_artist_post(post_or_id)
        rating_obj = ArtistPostRating.objects.get(post=post, rater=self)
        rating_obj_id, num_stars = rating_obj.id, rating_obj.num_stars
        rating_obj.delete()

        post.num_stars = F('num_stars') - num_stars
        post.save(update_fields=['num_stars']) 

        return rating_obj_id

    def remove_non_artist_post_rating(self, post_or_id):
        post = get_non_artist_post(post_or_id)
        rating_obj = NonArtistPostRating.objects.get(post=post, rater=self)
        rating_obj_id, num_stars = rating_obj.id, rating_obj.num_stars
        rating_obj.delete()

        post.num_stars = F('num_stars') - num_stars
        post.save(update_fields=['num_stars']) 
        
        return rating_obj_id
    
    def record_artist_post_download(self, post_or_id):
        if not self.can_download:
            raise ValidationError(
                _('Not permitted to download a post.'),
                code='not_permitted'
            )

        post = get_artist_post(post_or_id)
        download_obj = ArtistPostDownload.objects.create(post=post, downloader=self)
        post.num_downloads = F('num_downloads') + 1
        post.save(update_fields=['num_downloads'])

        return download_obj

    def record_non_artist_post_download(self, post_or_id):
        if not self.can_download:
            raise ValidationError(
                _('Not permitted to download a post.'),
                code='not_permitted'
            )

        post = get_non_artist_post(post_or_id)
        download_obj = NonArtistPostDownload.objects.create(post=post, downloader=self)
        post.num_downloads = F('num_downloads') + 1
        post.save(update_fields=['num_downloads'])
        
        return download_obj

    def bookmark_artist_post(self, post_or_id):
        post = get_artist_post(post_or_id)
        bookmark_obj = ArtistPostBookmark.objects.create(post=post, bookmarker=self)
        post.num_bookmarks = F('num_bookmarks') + 1
        post.save(update_fields=['num_bookmarks'])

        return bookmark_obj

    def bookmark_non_artist_post(self, post_or_id):
        post = get_non_artist_post(post_or_id)
        bookmark_obj = NonArtistPostBookmark.objects.create(post=post, bookmarker=self)
        post.num_bookmarks = F('num_bookmarks') + 1
        post.save(update_fields=['num_bookmarks'])
        
        return bookmark_obj
    
    def remove_artist_post_bookmark(self, post_or_id):
        post = get_artist_post(post_or_id)
        bookmark_obj = ArtistPostBookmark.objects.get(post=post, rater=self)
        bookmark_obj_id = bookmark_obj.id
        bookmark_obj.delete()

        post.num_bookmarks = F('num_bookmarks') - 1
        post.save(update_fields=['num_bookmarks'])

        return bookmark_obj_id

    def remove_artist_post_bookmark(self, post_or_id):
        post = get_non_artist_post(post_or_id)
        bookmark_obj = NonArtistPostBookmark.objects.get(post=post, rater=self)
        bookmark_obj_id = bookmark_obj.id
        bookmark_obj.delete()

        post.num_bookmarks = F('num_bookmarks') - 1
        post.save(update_fields=['num_bookmarks'])
        
        return bookmark_obj_id


class SuspensionOperations:
    """Mixin containing operations to be used on the Suspension model"""

    def end(self):
        if self.is_active:
            raise ValidationError(
                _('Suspension is still ongoing'),
                code='ongoing_suspension'
            )
            
        # Mark suspension as no longer active
        self.is_active = False
        self.save(update_fields=['is_active'])


