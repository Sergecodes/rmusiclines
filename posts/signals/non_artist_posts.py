from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from posts.models.non_artist_posts.models import (
    NonArtistPost, NonArtistPostDownload, NonArtistPostRepost,
    NonArtistPostComment, NonArtistPostCommentLike,
    NonArtistPostBookmark, NonArtistPostRating
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

@receiver(post_save, sender=NonArtistPostRating)
def increment_post_rating_count(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        post.num_stars = F('num_stars') + instance.num_stars
        post.save(update_fields=['num_stars']) 

@receiver(post_delete, sender=NonArtistPostRating)
def decrement_post_rating_count(sender, instance, **kwargs):
    post = instance.post
    post.num_stars = F('num_stars') - instance.num_stars
    post.save(update_fields=['num_stars']) 

@receiver(post_save, sender=NonArtistPostRepost)
def increment_post_repost_count(sender, instance, created, **kwargs):
    if created:
        post = instance.post

        if instance.comment:
            post.num_comment_reposts = F('num_comment_reposts') + 1
            post.save(update_fields=['num_comment_reposts'])
        else:
            post.num_simple_reposts = F('num_simple_reposts') + 1
            post.save(update_fields=['num_simple_reposts'])

@receiver(post_delete, sender=NonArtistPostRepost)
def decrement_post_repost_count(sender, instance, **kwargs):
    post = instance.post
		
    if instance.comment:
        post.num_comment_reposts = F('num_comment_reposts') - 1
        post.save(update_fields=['num_comment_reposts'])
    else:
        post.num_simple_reposts = F('num_simple_reposts') - 1
        post.save(update_fields=['num_simple_reposts'])

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
        post, poster = instance.post, instance.poster
        post.num_comments = F('num_comments') + 1
        post.save(update_fields=['num_comments'])
        poster.num_non_artist_post_comments = F('num_non_artist_post_comments') + 1
        poster.save(update_fields=['num_non_artist_post_comments'])

@receiver(post_delete, sender=NonArtistPostComment)
def decrement_post_comment_count(sender, instance, **kwargs):
    post, poster = instance.post, instance.poster
    post.num_comments = F('num_comments') - 1
    post.save(update_fields=['num_comments'])
    poster.num_non_artist_post_comments = F('num_non_artist_post_comments') - 1
    poster.save(update_fields=['num_non_artist_post_comments'])


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


