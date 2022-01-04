from actstream import action
from django.contrib.auth import get_user_model
from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from posts.models.artist_posts.models import (
    ArtistPost, ArtistPostDownload, ArtistPostRepost,
    ArtistPostComment, ArtistPostCommentLike,
    ArtistPostBookmark, ArtistPostRating
)
from posts.utils import extract_hashtags, extract_mentions

User = get_user_model()


@receiver(post_save, sender=ArtistPost)
def set_post_attributes(sender, instance, created, raw, using, update_fields, **kwargs):
    """Parse post and set related attributes such as users mentioned, hashtags, ..."""

    print(update_fields)

    # If object is newly created or body is updated
    # reset attributes of post.
    if created or (type(update_fields) is list and 'body' in update_fields):
        post = instance
        post_content = post.body
        
        post.hashtags.set(extract_hashtags(post_content))
        post.users_mentioned.set([
            User.objects.get(username=username) 
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


@receiver(post_save, sender=ArtistPost)
def increment_user_post_count(sender, instance, created, **kwargs):
    if created:
        poster = instance.poster
        poster.num_artist_posts = F('num_artist_posts') + 1
        poster.save(update_fields=['num_artist_posts'])


@receiver(post_delete, sender=ArtistPost)
def decrement_user_post_count(sender, instance, **kwargs):
    poster = instance.poster
    poster.num_artist_posts = F('num_artist_posts') - 1
    poster.save(update_fields=['num_artist_posts'])


@receiver(post_save, sender=ArtistPostComment)
def set_comment_attributes(sender, instance, created, raw, using, update_fields, **kwargs):
    print(update_fields)

    if created or (type(update_fields) is list and 'body' in update_fields):
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
            target=comment.post,
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


@receiver(post_save, sender=ArtistPostRepost)
def increment_post_repost_count(sender, instance, created, **kwargs):
    if created:
        post = instance.post

        if instance.comment:
            post.num_comment_reposts = F('num_comment_reposts') + 1
            post.save(update_fields=['num_comment_reposts'])
        else:
            post.num_simple_reposts = F('num_simple_reposts') + 1
            post.save(update_fields=['num_simple_reposts'])

        # Send action
        action.send(
            instance.reposter,
            verb=_('reposted'),
            target=post,
            action_object=instance
        )


@receiver(post_delete, sender=ArtistPostRepost)
def decrement_post_repost_count(sender, instance, **kwargs):
    post = instance.post
		
    if instance.comment:
        post.num_comment_reposts = F('num_comment_reposts') - 1
        post.save(update_fields=['num_comment_reposts'])
    else:
        post.num_simple_reposts = F('num_simple_reposts') - 1
        post.save(update_fields=['num_simple_reposts'])


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
    if created:
        if instance.is_parent:
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


