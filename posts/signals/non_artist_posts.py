from actstream import action
from django.contrib.auth import get_user_model
from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from posts.models.non_artist_posts.models import (
    NonArtistPost, NonArtistPostDownload,
    NonArtistPostComment, NonArtistPostCommentLike,
    NonArtistPostBookmark, NonArtistPostRating
)
from posts.utils import extract_hashtags, extract_mentions

User = get_user_model()


@receiver(post_save, sender=NonArtistPost)
def set_post_attributes(sender, instance, created, **kwargs):
    """Parse post and set related attributes such as users mentioned, hashtags, ..."""

    update_fields = kwargs.get('update_fields')
    if not update_fields:
        update_fields = []

    post = instance

    # If post is a parent post
    if post.is_parent:
        # If object is newly created or body is updated
        # reset attributes of post.
        if created or 'body' in update_fields:
            post_content = post.body
            
            post.hashtags.set(extract_hashtags(post_content))
            post.users_mentioned.set([
                User.objects.get(username=username) \
                for username in extract_mentions(post_content)
            ])
        
        # Add action
        if created:
            action.send(
                post.poster,
                verb=_('posted'),
                target=post,
            )

    # Else if post is just a simple repost
    elif post.is_simple_repost:
        if created:
            parent_post = post.parent
            parent_post.num_simple_reposts = F('num_simple_reposts') + 1
            parent_post.save(update_fields=['num_simple_reposts'])

            action.send(
                post.poster,
                verb=_('shared'),  # Poster reposted post (poster shared post)
                target=post
            )
    
    # Else if post is not a simple repost(is repost with body)
    elif not post.is_simple_repost:
        if created:
            parent_post = post.parent
            parent_post.num_non_simple_reposts = F('num_non_simple_reposts') + 1
            parent_post.save(update_fields=['num_non_simple_reposts'])

            action.send(
                post.poster,
                verb=_('reposted'), 
                target=post
            )


@receiver(post_save, sender=NonArtistPost)
def increment_user_post_count(sender, instance, created, **kwargs):
    if created:
        poster = instance.poster
        poster.num_non_artist_posts = F('num_non_artist_posts') + 1
        poster.save(update_fields=['num_non_artist_posts'])


@receiver(post_delete, sender=NonArtistPost)
def decrement_user_post_count(sender, instance, **kwargs):
    poster = instance.poster
    poster.num_non_artist_posts = F('num_non_artist_posts') - 1
    poster.save(update_fields=['num_non_artist_posts'])


@receiver(post_delete, sender=NonArtistPost)
def decrement_post_repost_count(sender, instance: NonArtistPost, **kwargs):
    """Decrement parent post's number of reposts if deleted post is a repost."""
    post = instance

    if not post.is_parent:
        parent_post = post.parent

        if post.is_simple_repost:
            parent_post.num_simple_reposts = F('num_simple_reposts') - 1
            parent_post.save(update_fields=['num_simple_reposts'])
        else:
            parent_post.num_non_simple_reposts = F('num_non_simple_reposts') - 1
            parent_post.save(update_fields=['num_non_simple_reposts'])


@receiver(post_save, sender=NonArtistPostComment)
def set_comment_mentioned_users(sender, instance, created, **kwargs):
    update_fields = kwargs.get('update_fields')
    if not update_fields:
        update_fields = []

    if created or 'body' in update_fields:
        comment = instance
        comment.users_mentioned.set([
            User.objects.get(username=username) 
            for username in extract_mentions(comment.body)
        ])

    # Add action
    if created:
        action.send(
            comment.poster,
            verb='commented on',
            target=comment.post_concerned,
            action_object=comment
        )


@receiver(post_save, sender=NonArtistPostRating)
def increment_post_rating_count(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        post.num_stars = F('num_stars') + instance.num_stars
        post.save(update_fields=['num_stars']) 

        # Add action
        action.send(
            instance.rater, 
            verb=_('rated'),
            target=post,
            action_object=instance
        )


@receiver(post_delete, sender=NonArtistPostRating)
def decrement_post_rating_count(sender, instance, **kwargs):
    post = instance.post
    post.num_stars = F('num_stars') - instance.num_stars
    post.save(update_fields=['num_stars']) 


@receiver(post_save, sender=NonArtistPostBookmark)
def increment_post_bookmark_count(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        post.num_bookmarks = F('num_bookmarks') + 1
        post.save(update_fields=['num_bookmarks'])


@receiver(post_delete, sender=NonArtistPostBookmark)
def decrement_post_bookmark_count(sender, instance, **kwargs):
    post = instance.post
    post.num_bookmarks = F('num_bookmarks') - 1
    post.save(update_fields=['num_bookmarks'])


@receiver(post_save, sender=NonArtistPostDownload)
def increment_post_download_count(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        post.num_downloads = F('num_downloads') + 1
        post.save(update_fields=['num_downloads'])


@receiver(post_delete, sender=NonArtistPostDownload)
def decrement_post_download_count(sender, instance, **kwargs):
    # Decrementing the num_downloads of a post doesn't make sense 
    # since it has already been downloaded to "user's" storage.
    pass


@receiver(post_save, sender=NonArtistPostComment)
def increment_post_comment_count(sender, instance, created, **kwargs):
    if created:
        if instance.is_parent:
            post, poster = instance.post_concerned, instance.poster

            post.num_parent_comments = F('num_parent_comments') + 1
            post.save(update_fields=['num_parent_comments'])
            poster.num_parent_non_artist_post_comments = F('num_parent_non_artist_post_comments') + 1
            poster.save(update_fields=['num_parent_non_artist_post_comments'])


@receiver(post_delete, sender=NonArtistPostComment)
def decrement_post_comment_count(sender, instance, **kwargs):
    if instance.is_parent:
        post, poster = instance.post_concerned, instance.poster

        post.num_parent_comments = F('num_parent_comments') - 1
        post.save(update_fields=['num_parent_comments'])
        poster.num_parent_non_artist_post_comments = F('num_parent_non_artist_post_comments') - 1
        poster.save(update_fields=['num_parent_non_artist_post_comments'])


@receiver(post_save, sender=NonArtistPostCommentLike)
def increment_comment_like_count(sender, instance, created, **kwargs):
    if created:
        comment = instance.comment
        comment.num_likes = F('num_likes') + 1
        comment.save(update_fields=['num_likes'])


@receiver(post_delete, sender=NonArtistPostCommentLike)
def decrement_comment_like_count(sender, instance, **kwargs):
    comment = instance.comment
    comment.num_likes = F('num_likes') - 1
    comment.save(update_fields=['num_likes'])


