# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-08 23:16
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sb', '0002_auto_20160408_2308'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='changed_at',
            field=models.DateTimeField(auto_now=True, default=datetime.datetime(2016, 4, 8, 23, 16, 25, 320085, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='song',
            name='changed_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='last_changed_songs', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='song',
            name='suggested_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2016, 4, 8, 23, 16, 51, 892654, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='song',
            name='suggested_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='suggested_songs', to=settings.AUTH_USER_MODEL),
        ),
    ]