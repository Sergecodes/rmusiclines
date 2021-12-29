from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from posts.models.artist_posts.models import (
    ArtistPost, ArtistPostDownload, ArtistPostRepost,
    ArtistPostComment, ArtistPostCommentLike,
    ArtistPostBookmark, ArtistPostRating
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

@receiver(post_save, sender=ArtistPostRating)
def increment_post_rating_count(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        post.num_stars = F('num_stars') + instance.num_stars
        post.save(update_fields=['num_stars']) 

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
        post, poster = instance.post, instance.poster
        post.num_comments = F('num_comments') + 1
        post.save(update_fields=['num_comments'])
        poster.num_artist_post_comments = F('num_artist_post_comments') + 1
        poster.save(update_fields=['num_artist_post_comments'])

@receiver(post_delete, sender=ArtistPostComment)
def decrement_post_comment_count(sender, instance, **kwargs):
    post, poster = instance.post, instance.poster
    post.num_comments = F('num_comments') - 1
    post.save(update_fields=['num_comments'])
    poster.num_artist_post_comments = F('num_artist_post_comments') - 1
    poster.save(update_fields=['num_artist_post_comments'])


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


