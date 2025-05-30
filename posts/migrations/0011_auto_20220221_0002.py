# Generated by Django 3.2.9 on 2022-02-21 00:02

import core.fields
import django.core.validators
from django.db import migrations
import easy_thumbnails.fields
import posts.models.artist_posts.models
import posts.models.non_artist_posts.models
import posts.validators


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_auto_20220219_0354'),
    ]

    operations = [
        migrations.AlterField(
            model_name='artistpostphoto',
            name='photo',
            field=easy_thumbnails.fields.ThumbnailerImageField(height_field='photo_height', upload_to=posts.models.artist_posts.models.artist_post_photo_upload_path, validators=[django.core.validators.FileExtensionValidator(['png, jpg, gif']), posts.validators.validate_post_photo_file], width_field='photo_width'),
        ),
        migrations.AlterField(
            model_name='artistpostvideo',
            name='video',
            field=core.fields.DynamicStorageFileField(upload_to=posts.models.artist_posts.models.artist_post_video_upload_path, validators=[django.core.validators.FileExtensionValidator(['mp4', 'mov']), posts.validators.validate_post_video_file]),
        ),
        migrations.AlterField(
            model_name='nonartistpostphoto',
            name='photo',
            field=easy_thumbnails.fields.ThumbnailerImageField(height_field='photo_height', upload_to=posts.models.non_artist_posts.models.non_artist_post_photo_upload_path, validators=[django.core.validators.FileExtensionValidator(['png, jpg, gif']), posts.validators.validate_post_photo_file], width_field='photo_width'),
        ),
        migrations.AlterField(
            model_name='nonartistpostvideo',
            name='video',
            field=core.fields.DynamicStorageFileField(upload_to=posts.models.non_artist_posts.models.non_artist_post_video_upload_path, validators=[django.core.validators.FileExtensionValidator(['mp4', 'mov']), posts.validators.validate_post_video_file]),
        ),
    ]
