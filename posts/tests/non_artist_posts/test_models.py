import datetime
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from posts.models.non_artist_posts.models import (
    NonArtistPost, NonArtistPostVideo
)
from posts.utils import get_video_resolution, get_video_duration

User = get_user_model()


def create_test_user(self, username, email, display_name, birth_date, country, **extra_fields):
    return User.objects.create_user(
        username=username,
        email=email,
        display_name=display_name,
        birth_date=birth_date,
        country=country,
        **extra_fields
    )


class PostMedia(TestCase):
    def create_post(self):
        return NonArtistPost.objects.create(
            body=f"Hello this is a non artist post",
            poster=create_test_user(
                'user1', 'email1@gmail.com', 'name name1', 
                datetime.datetime(year=2000, month=3, day=8),
                'CM', is_active=True
            ),
        )

    def test_post_video_duration(self):
        """Validate video format and size"""

        video = SimpleUploadedFile(
            'posts/tests/media/video_file.mp4',
            'file_content',
            content_type='video/mp4'
        )
        post_video = NonArtistPostVideo.objects.create(
            post=self.create_post,
            video=video,
        )

        self.assertTrue(post_video, NonArtistPostVideo.objects.get())


class PostAttributes(TestCase):
    # def create_artist_post(self):
    #     user1 = self.create_test_user(
    #         'user1', 'email1@gmail.com', 'name name1', 
    #         datetime.datetime(year=2000, month=3, day=8),
    #         'CM', is_active=True
    #     )
    #     user2 = self.create_test_user(
    #         'user2', 'email2@gmail.com', 'name name2', 
    #         datetime.datetime(year=2001, month=3, day=8),
    #         'CM', is_active=True
    #     )
    #     return NonArtistPost.objects.create(
    #         body=f"Hello @{user2.username}, this is a post with hashtags #one #123 #i_love #fuckoff",
    #         poster=user1,
    #     )
    pass




