from actstream import action
from django.contrib.auth import get_user_model
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from posts.models.non_artist_posts.models import NonArtistPost, NonArtistPostComment
from posts.utils import extract_hashtags, extract_mentions

User = get_user_model()


@receiver(post_save, sender=NonArtistPost)
def set_post_attributes(sender, instance, created, **kwargs):
    """Parse post and set related attributes such as users mentioned, hashtags, ..."""

    update_fields = kwargs.get('update_fields')
    if not update_fields:
        update_fields = []

    post, poster = instance, instance.poster

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
            # Increment user repost count
            poster.num_non_artist_posts = F('num_non_artist_posts') + 1
            poster.save(update_fields=['num_non_artist_posts'])

            action.send(
                poster,
                verb=_('posted'),
                target=post,
            )

    # If post is a repost
    else:
        if post.is_simple_repost:
            if created:
                parent_post = post.parent
                parent_post.num_simple_reposts = F('num_simple_reposts') + 1
                parent_post.save(update_fields=['num_simple_reposts'])

                action.send(
                    poster,
                    verb=_('shared'),  # Poster reposted post (poster shared post)
                    target=parent_post,
                    action_object=post
                )

        else:
            if created:
                parent_post = post.parent
                parent_post.num_non_simple_reposts = F('num_non_simple_reposts') + 1
                parent_post.save(update_fields=['num_non_simple_reposts'])

                action.send(
                    poster,
                    verb=_('reposted'), 
                    target=parent_post,
                    action_object=post
                )

        # Update user repost count
        poster.num_non_artist_post_reposts = F('num_non_artist_post_reposts') + 1
        poster.save(update_fields=['num_non_artist_post_reposts'])

        # TODO Notify post owner of reposts...
        


@receiver(post_save, sender=NonArtistPostComment)
def set_comment_attributes(sender, instance: NonArtistPostComment, created, **kwargs):
    update_fields = kwargs.get('update_fields')
    if not update_fields:
        update_fields = []

    comment = instance

    if created or 'body' in update_fields:
        comment.users_mentioned.set([
            User.objects.get(username=username) 
            for username in extract_mentions(comment.body)
        ])

    if created:
        poster, post = comment.poster, comment.post_concerned

        # Increment post comment count
        if comment.is_ancestor:
            post.num_ancestor_comments = F('num_ancestor_comments') + 1
            post.save(update_fields=['num_ancestor_comments'])
            poster.num_ancestor_non_artist_post_comments = F('num_ancestor_non_artist_post_comments') + 1
            poster.save(update_fields=['num_ancestor_non_artist_post_comments'])
        else:
            ancestor = comment.ancestor
            ancestor.num_child_comments = F('num_child_comments') + 1
            ancestor.save(update_fields=['num_child_comments'])

        # Add action
        action.send(
            comment.poster,
            verb='commented on',
            target=post,
            action_object=comment
        )

