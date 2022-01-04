from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from posts.models.artist_posts.models import (
    ArtistPost, ArtistPostVideo
)


# class ArtistPostMedia(TestCase):
#     def create_artist_post(self):
#         return ArtistPost.objects.create(
#             body="Hello, this is a post with hashtags #one #123 #i_love #fuckoff"
#         )

#     def test_upload_video(self):
#         """Validate video format and size"""

#         video = SimpleUploadedFile(
#             'posts/tests/media/video_file.mp4',
#             'file_content',
#             content_type='video/mp4'
        # )

