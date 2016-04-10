from django.contrib import admin
from django.contrib.auth.models import User

from sb import models


class PlaysInline(admin.TabularInline):
    model = models.UserPlays


class UserWithInlines(admin.ModelAdmin):
    inlines = [
        PlaysInline,
    ]


class SongLinkInline(admin.TabularInline):
    model = models.SongLink


class SongPartInline(admin.TabularInline):
    model = models.SongPart


class SongWatcherInline(admin.TabularInline):
    model = models.SongWatcher


class SongWithInlines(admin.ModelAdmin):
    inlines = [
        SongLinkInline, SongPartInline, SongWatcherInline,
    ]


admin.site.unregister(User)
admin.site.register(User, UserWithInlines)

admin.site.register(models.Instrument)

admin.site.register(models.Song, SongWithInlines)
