from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
from django.core.urlresolvers import reverse
from django.core import validators

import sbgig.models


class Instrument(models.Model):
    name = models.CharField(verbose_name=_("Instrument name"),
                            max_length=100, null=False, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("instrument")

    def __str__(self):
        return self.name


class Song(models.Model):
    gig = models.ForeignKey(sbgig.models.Gig, on_delete=models.CASCADE,
                            blank=True, null=True, related_name='songs')
    suggested_by = models.ForeignKey(User, on_delete=models.PROTECT,
                                     null=False, blank=False,
                                     related_name='suggested_songs')
    suggested_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT,
                                   null=False, blank=False,
                                   related_name='last_changed_songs')
    title = models.CharField(verbose_name=_("Title"),
                             max_length=150, null=False, blank=False)
    artist = models.CharField(verbose_name=_("Artist"),
                              max_length=100, null=False, blank=True)
    description = models.TextField(verbose_name=_("Description"),
                                   null=False, blank=True)
    lyrics = models.TextField(null=False, blank=True)
    staffed = models.BooleanField(null=False, blank=False, default=False)
    readiness = models.PositiveSmallIntegerField(
        blank=False, default=0, validators=[validators.MaxValueValidator(100)]
    )

    class Meta:
        index_together = [
            ('gig', 'staffed'),
        ]

    def __init__(self, *args, **kwargs):
        super(Song, self).__init__(*args, **kwargs)
        self._pristine = {
            field: getattr(self, field)
            for field in ('title', 'artist', 'description',
                          'lyrics', 'staffed')
        }

    def __str__(self):
        if self.artist:
            return "%s (by %s)" % (self.title, self.artist)
        else:
            return self.title

    def get_absolute_url(self):
        return reverse('sbsong:view-song', args=[self.id])


class SongWatcher(models.Model):
    song = models.ForeignKey(Song, blank=False, related_name='watchers',
                             on_delete=models.CASCADE)
    user = models.ForeignKey(User, blank=False, related_name='watched_songs',
                             on_delete=models.CASCADE)
    last_seen = models.DateTimeField(blank=False, auto_now_add=True)

    class Meta:
        unique_together = [
            ('song', 'user'),
        ]


class SongLink(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE,
                             null=False, blank=False, related_name='links')
    link = models.URLField(null=False, blank=False, verbose_name=_("Link"))
    notice = models.CharField(max_length=150, null=False, blank=True,
                              verbose_name=_("Notice"))

    def __str__(self):
        link = self.link
        if len(link) > 60:
            link = link[:60] + '...'
        if self.notice:
            return "%s (%s)" % (link, self.notice)
        else:
            return link


class SongPart(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE,
                             null=False, blank=False, related_name='parts')
    instrument = models.ForeignKey(Instrument, on_delete=models.PROTECT,
                                   verbose_name=_("Instrument"),
                                   null=False, blank=False)
    notice = models.CharField(verbose_name=_("Notice"),
                              max_length=200, null=False, blank=True)
    required = models.BooleanField(verbose_name=_("Required"),
                                   blank=False, null=False, default=True)

    def __str__(self):
        if self.notice:
            res = "%s (%s)" % (self.instrument.name, self.notice)
        else:
            res = self.instrument.name
        if self.required:
            return res + "*"
        else:
            return res


class SongPerformer(models.Model):
    READINESS_STRINGS = {
        0: ugettext_noop("Haven't seen"),
        25: ugettext_noop("Scratched a bit"),
        50: ugettext_noop("Peep into the text/chords"),
        75: ugettext_noop("Mostly learned"),
        100: ugettext_noop("Mastered"),
    }
    READINESS_CHOICES = sorted((k, _(v)) for k, v in READINESS_STRINGS.items())

    part = models.ForeignKey(SongPart, on_delete=models.CASCADE,
                             null=False, blank=False)
    performer = models.ForeignKey(User, on_delete=models.CASCADE,
                                  null=True, blank=True)
    notice = models.CharField(max_length=200, null=False, blank=True)
    readiness = models.PositiveSmallIntegerField(blank=False, default=0,
                                                 choices=READINESS_CHOICES)

    class Meta:
        unique_together = [
            ('part', 'performer'),
        ]

    def __str__(self):
        if self.notice:
            return "%s (%s)" % (self.performer.username, self.notice)
        else:
            return self.performer.username
