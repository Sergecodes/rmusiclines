# Generated by Django 3.2.9 on 2022-02-11 10:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_alter_taggedartist_tag'),
    ]

    operations = [
        migrations.RenameField(
            model_name='suspension',
            old_name='user',
            new_name='suspended_user',
        ),
        migrations.AlterField(
            model_name='suspension',
            name='reason',
            field=models.TextField(),
        ),
    ]
