# Generated by Django 3.2.9 on 2022-02-11 06:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_auto_20220209_1044'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hashtaggedartistpost',
            name='tag',
            field=models.ForeignKey(db_column='post_hashtag_id', on_delete=django.db.models.deletion.CASCADE, related_name='hashtagged_artist_posts', to='posts.posthashtag'),
        ),
        migrations.AlterField(
            model_name='hashtaggednonartistpost',
            name='tag',
            field=models.ForeignKey(db_column='post_hashtag_id', on_delete=django.db.models.deletion.CASCADE, related_name='hashtagged_non_artist_posts', to='posts.posthashtag'),
        ),
    ]
