from django.contrib import admin

from sbsong import models


class SongLinkInline(admin.TabularInline):
    model = models.SongLink


class SongPartInline(admin.TabularInline):
    model = models.SongPart


class SongWithInlines(admin.ModelAdmin):
    inlines = [
        SongLinkInline, SongPartInline,
    ]


admin.site.register(models.Instrument)

admin.site.register(models.Song, SongWithInlines)
