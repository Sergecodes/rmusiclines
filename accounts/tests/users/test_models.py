import datetime
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models.artists.models import Artist
from posts.models.artist_posts.models import ArtistPost
from posts.models.non_artist_posts.models import NonArtistPost

User = get_user_model() 


class TestUtils:
    @classmethod
    def create_test_user(
        cls, username, email, password, 
        display_name, birth_date, country, 
        **extra_fields
    ):
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            display_name=display_name,
            birth_date=birth_date,
            country=country,
            **extra_fields
        )

    @classmethod
    def create_artist(cls, name, birth_date, country, **extra_fields):
        return Artist.objects.create(
            name=name,
            birth_date=birth_date,
            country=country,
            **extra_fields
        )

    @classmethod
    def create_artist_post(cls, artist, body, poster, **extra_fields):
        return ArtistPost.objects.create(
            artist=artist,
            body=body,
            poster=poster,
            **extra_fields
        )

    @classmethod
    def create_non_artist_post(cls, body, poster, **extra_fields):
        return NonArtistPost.objects.create(
            body=body,
            poster=poster,
            **extra_fields
        )


class UserAttributesTests(TestCase):
    """Test User attributes(fields)"""

    def test_pinning_artist_and_non_artist_post(self):
        user = TestUtils.create_test_user(
            'user1', 'email1@gmail.com', 'password', 'name name1', 
            datetime.datetime(year=2000, month=3, day=8), 'CM', is_active=True
        )
        artist = TestUtils.create_artist(
            'artist name', 
            datetime.datetime(year=1996, month=8, day=8),
            'US'
        )
        artist_post = TestUtils.create_artist_post(artist, 'This is an artist post', user)
        non_artist_post = TestUtils.create_non_artist_post('This is a non artist post', user)

        # Pin artist post then non artist post
        user.pinned_artist_post = artist_post
        user.pinned_non_artist_post = non_artist_post
        
        try:
            user.save()
            self.assertIsNotNone(user.pinned_artist_post)
            self.assertIsNotNone(user.non_pinned_artist_post)
        except ValidationError:
            self.fail("Failed to pin artist post and non artist post")
            
        
