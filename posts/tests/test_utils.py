import os
from django.conf import settings
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
from django.test import TestCase

from posts.utils import get_video_resolution, get_video_duration


class VideoTests(TestCase):
    def test_video_duration(self):
        # file = open(os.path.join(settings.BASE_DIR, 'posts/tests/media/video_file.mp4'), 'rb')
        # video = SimpleUploadedFile(
        #     os.path.join(settings.BASE_DIR, 'posts/tests/media/video_file.mp4'),
        #     file.read(),
        #     content_type='video/mp4'
        # )
        # Apparently, file must be saved before manipulating using opencv
        f = File(os.path.join(settings.BASE_DIR, 'posts/tests/media/video_file.mp4'))
        video = f.file

        self.assertTrue(get_video_duration(video), (301, '0:05:01'))

    def test_video_resolution(self):
        f = File(os.path.join(settings.BASE_DIR, 'posts/tests/media/video_file.mp4'))
        video = f.file

        self.assertTrue(get_video_resolution(video), (1280, 720))

