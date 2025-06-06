# Generated by Django 3.2.9 on 2022-02-19 03:54

import core.fields
import django.core.validators
from django.db import migrations, models
import posts.validators


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_auto_20220212_0825'),
    ]

    operations = [
        migrations.AddField(
            model_name='artistpostvideo',
            name='was_audio',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name='nonartistpostvideo',
            name='was_audio',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AlterField(
            model_name='artistpostvideo',
            name='video',
            field=core.fields.DynamicStorageFileField(upload_to='artist_posts_videos/', validators=[django.core.validators.FileExtensionValidator(['mp4', 'mov']), posts.validators.validate_post_video_file]),
        ),
        migrations.AlterField(
            model_name='nonartistpostvideo',
            name='video',
            field=core.fields.DynamicStorageFileField(upload_to='non_artist_posts_videos/', validators=[django.core.validators.FileExtensionValidator(['mp4', 'mov']), posts.validators.validate_post_video_file]),
        ),
    ]
