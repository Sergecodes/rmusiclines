from django.core.cache import cache
from django.core.files.base import ContentFile

from core.constants import FILE_STORAGE_CLASS
from core.utils import get_user_cache_keys
from posts.constants import FORM_AND_UPLOAD_DIR
from posts.models.artist_posts.models import ArtistPostPhoto, ArtistPostVideo, ArtistPost

STORAGE = FILE_STORAGE_CLASS()


def store_artist_post_cache_media(username, post: ArtistPost):
    """
    Store media that's in cache to post and clear cache. 
    Used by graphql artist post and repost mutations.
    """
    # Get user cache keys
    user_cache_keys = get_user_cache_keys(username)
    cache_photos_key, cache_video_key = user_cache_keys['photos'], user_cache_keys['video']

    # Save photos in cache(if any) to post
    save_dir = FORM_AND_UPLOAD_DIR['artist_post_photo']
    user_photos_list = cache.get(cache_photos_key, [])

    # Bulk create photos. Note that one of its caveats is that custom save method 
    # is not called; but since we have no custom save method, no worries then.
    post_photos = []
    for photo_dict in user_photos_list:
        img_file = ContentFile(photo_dict['file_bytes'])
        saved_filename = STORAGE.save(save_dir + photo_dict['filename'], img_file)
        post_photos.append(ArtistPostPhoto(post=post, photo=saved_filename))

    # If no photos were uploaded hence 'post_photos' is empty, there will be no prob
    ArtistPostPhoto.objects.bulk_create(post_photos)

    # Save videos that are in cache to post
    # TODO Call external api (aws elastic video encoder) to compress video

    video_dict = cache.get(cache_video_key, {})
    if video_dict:
        ArtistPostVideo.objects.create(
            post=post,
            video=video_dict['filepath'], 
            was_audio=video_dict['was_audio']
        )

    # Clear cache
    cache.delete(cache_photos_key)
    cache.delete(cache_video_key)

