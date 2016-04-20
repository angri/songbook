# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-19 23:39
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sb', '0005_auto_20160410_2338'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='songcomment',
            options={'ordering': ['song', '-datetime']},
        ),
        migrations.AlterField(
            model_name='songcomment',
            name='comment_type',
            field=models.CharField(choices=[('regular', 'regular comment'), ('song_changed', 'song edit')], default='regular', max_length=20),
        ),
        migrations.AlterField(
            model_name='songcomment',
            name='song',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='sb.Song'),
        ),
        migrations.AlterField(
            model_name='songlink',
            name='song',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='links', to='sb.Song'),
        ),
        migrations.AlterField(
            model_name='userplays',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plays', to=settings.AUTH_USER_MODEL),
        ),
    ]
