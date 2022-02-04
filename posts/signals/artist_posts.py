from actstream import action
from django.contrib.auth import get_user_model
from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from posts.models.artist_posts.models import (
    ArtistPost, ArtistPostDownload,
    ArtistPostComment, ArtistPostCommentLike,
    ArtistPostBookmark, ArtistPostRating
)
from posts.utils import extract_hashtags, extract_mentions

User = get_user_model()


@receiver(post_save, sender=ArtistPost)
def set_post_attributes(sender, instance: ArtistPost, created: bool, **kwargs):
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

            action.send(
                post.artist,
                verb=_('has new post'),
                target=post
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


@receiver(post_save, sender=ArtistPost)
def increment_user_post_count(sender, instance, created, **kwargs):
    if created:
        poster = instance.poster
        poster.num_artist_posts = F('num_artist_posts') + 1
        poster.save(update_fields=['num_artist_posts'])


@receiver(post_delete, sender=ArtistPost)
def decrement_user_post_count(sender, instance, **kwargs):
    """Decrement user's number of artist posts"""
    poster = instance.poster
    poster.num_artist_posts = F('num_artist_posts') - 1
    poster.save(update_fields=['num_artist_posts'])


@receiver(post_delete, sender=ArtistPost)
def decrement_post_repost_count(sender, instance, **kwargs):
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


@receiver(post_save, sender=ArtistPostComment)
def set_comment_attributes(sender, instance, created, **kwargs):
    # Note that update_fields will always be in kwargs since it is a part of the 
    # function parameters, but it will be None(it won't be an empty list )
    # if it does not contain any fields.
    # So if the field is None, set it to an empty list
    update_fields = kwargs.get('update_fields')
    if not update_fields:
        update_fields = []

    if created or 'body' in update_fields:
        comment = instance
        comment.users_mentioned.set([
            User.objects.get(username=username) \
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


@receiver(post_save, sender=ArtistPostRating)
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


@receiver(post_delete, sender=ArtistPostRating)
def decrement_post_rating_count(sender, instance, **kwargs):
    post = instance.post
    post.num_stars = F('num_stars') - instance.num_stars
    post.save(update_fields=['num_stars']) 


@receiver(post_save, sender=ArtistPostBookmark)
def increment_post_bookmark_count(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        post.num_bookmarks = F('num_bookmarks') + 1
        post.save(update_fields=['num_bookmarks'])


@receiver(post_delete, sender=ArtistPostBookmark)
def decrement_post_bookmark_count(sender, instance, **kwargs):
    post = instance.post
    post.num_bookmarks = F('num_bookmarks') - 1
    post.save(update_fields=['num_bookmarks'])


@receiver(post_save, sender=ArtistPostDownload)
def increment_post_download_count(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        post.num_downloads = F('num_downloads') + 1
        post.save(update_fields=['num_downloads'])


@receiver(post_delete, sender=ArtistPostDownload)
def decrement_post_download_count(sender, instance, **kwargs):
    # Decrementing the num_downloads of a post doesn't make sense 
    # since it has already been downloaded to "user's" storage.
    pass


@receiver(post_save, sender=ArtistPostComment)
def increment_post_comment_count(sender, instance, created, **kwargs):
    if created and instance.is_parent:
        post, poster = instance.post_concerned, instance.poster

        post.num_parent_comments = F('num_parent_comments') + 1
        post.save(update_fields=['num_parent_comments'])
        poster.num_parent_artist_post_comments = F('num_parent_artist_post_comments') + 1
        poster.save(update_fields=['num_parent_artist_post_comments'])


@receiver(post_delete, sender=ArtistPostComment)
def decrement_post_comment_count(sender, instance, **kwargs):
    if instance.is_parent:
        post, poster = instance.post_concerned, instance.poster
    
        post.num_parent_comments = F('num_parent_comments') - 1
        post.save(update_fields=['num_parent_comments'])
        poster.num_parent_artist_post_comments = F('num_parent_artist_post_comments') - 1
        poster.save(update_fields=['num_parent_artist_post_comments'])


@receiver(post_save, sender=ArtistPostCommentLike)
def increment_comment_like_count(sender, instance, created, **kwargs):
    if created:
        comment = instance.comment
        comment.num_likes = F('num_likes') + 1
        comment.save(update_fields=['num_likes'])


@receiver(post_delete, sender=ArtistPostCommentLike)
def decrement_comment_like_count(sender, instance, **kwargs):
    comment = instance.comment
    comment.num_likes = F('num_likes') - 1
    comment.save(update_fields=['num_likes'])


