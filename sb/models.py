from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


class Instrument(models.Model):
    name = models.CharField(_("Instrument name"),
                            max_length=100, null=False, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("instrument")

    def __str__(self):
        return self.name


class UserPlays(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             null=False, blank=False)
    instrument = models.ForeignKey(Instrument, on_delete=models.PROTECT,
                                   null=False, blank=False)
    notice = models.CharField(max_length=150, null=False, blank=True)

    class Meta:
        unique_together = [
            ('user', 'instrument'),
        ]


class Song(models.Model):
    suggested_by = models.ForeignKey(User, on_delete=models.PROTECT,
                                     null=False, blank=False,
                                     related_name='suggested_songs')
    suggested_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT,
                                   null=False, blank=False,
                                   related_name='last_changed_songs')
    artist = models.CharField(max_length=100, null=False, blank=True)
    title = models.CharField(max_length=150, null=False, blank=False)
    description = models.TextField(null=False, blank=True)
    lyrics = models.TextField(null=False, blank=True)

    def __str__(self):
        if self.artist:
            return "%s (by %s)" % (self.title, self.artist)
        else:
            return self.title


class SongWatcher(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE,
                             null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             null=False, blank=False)

    class Meta:
        unique_together = [
            ('user', 'song'),
        ]


class SongLink(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE,
                             null=False, blank=False)
    link = models.URLField(null=False, blank=False)
    notice = models.CharField(max_length=150, null=False, blank=True)

    class Meta:
        unique_together = [
            ('song', 'link'),
        ]


class SongPart(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE,
                             null=False, blank=False, related_name='parts')
    instrument = models.ForeignKey(Instrument, on_delete=models.PROTECT,
                                   null=False, blank=False)
    notice = models.CharField(max_length=200, null=False, blank=True)


class SongPerformer(models.Model):
    part = models.ForeignKey(SongPart, on_delete=models.CASCADE,
                             null=False, blank=False)
    performer = models.ForeignKey(User, on_delete=models.CASCADE,
                                  null=True, blank=True)
    notice = models.CharField(max_length=200, null=False, blank=True)

    class Meta:
        unique_together = [
            ('part', 'performer'),
        ]


class SongComment(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE,
                             blank=False, null=False)
    author = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    datetime = models.DateTimeField(auto_now_add=True)
    text = models.TextField(null=False, blank=False)
