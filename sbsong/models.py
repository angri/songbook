import json

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
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
    changed_at = models.DateTimeField(auto_now=True)
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
    link = models.URLField(null=False, blank=False)
    notice = models.CharField(max_length=150, null=False, blank=True)

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


class SongActions:
    @classmethod
    def suggested_song(cls, user, song):
        action = (ugettext_noop('%(who)s (f) suggested a song %(when)s')
                  if user.profile.gender == 'f' else
                  ugettext_noop('%(who)s (m) suggested a song %(when)s'))
        changes = [
            {'title': ugettext_noop('Artist'),
             'title_translatable': True,
             'prev': '',
             'new': song.artist},
            {'title': ugettext_noop('Title'),
             'title_translatable': True,
             'prev': '',
             'new': song.title},
            {'title': ugettext_noop('Description'),
             'title_translatable': True,
             'prev': '',
             'new': song.description},
        ]
        cls._song_changed(song, action, user, changes)

    @classmethod
    def joined_part(cls, user, part, old_performers):
        action = (ugettext_noop('%(who)s (f) joined a song part %(when)s')
                  if user.profile.gender == 'f' else
                  ugettext_noop('%(who)s (m) joined a song part %(when)s'))
        return cls._part_participation_base(action, user, part, old_performers)

    @classmethod
    def edited_part_participation(cls, user, part, old_performers):
        action = (
            ugettext_noop('%(who)s (f) edited part participation %(when)s')
            if user.profile.gender == 'f' else
            ugettext_noop('%(who)s (m) edited part participation %(when)s')
        )
        return cls._part_participation_base(action, user, part, old_performers)

    @classmethod
    def left_part(cls, user, part, old_performers):
        action = (ugettext_noop('%(who)s (f) left a song part %(when)s')
                  if user.profile.gender == 'f' else
                  ugettext_noop('%(who)s (m) left a song part %(when)s'))
        return cls._part_participation_base(action, user, part, old_performers)

    @classmethod
    def _part_participation_base(cls, action, user, part, old_performers):
        new_performers = part.songperformer_set.all()
        changes = [
            {'title': str(part),
             'title_translatable': False,
             'prev': '\n'.join(sorted(str(songperformer)
                                      for songperformer in old_performers)),
             'new': '\n'.join(sorted(str(songperformer)
                                     for songperformer in new_performers))}
        ]
        old_performers_by_id = {sp.id: sp for sp in old_performers}
        for songperf in new_performers:
            old_performer = old_performers_by_id.pop(songperf.id, None)
            old_readiness = (
                SongPerformer.READINESS_STRINGS[old_performer.readiness]
                if old_performer is not None
                else ''
            )
            changes.append({
                'title': "%s / %s" % (songperf, songperf.part),
                'title_translatable': False,
                'prev': old_readiness,
                'new': SongPerformer.READINESS_STRINGS[songperf.readiness],
                'value_translatable': True,
            })
        for sp_id, songperf in sorted(old_performers_by_id.items()):
            changes.append({
                'title': "%s / %s" % (songperf, songperf.part),
                'title_translatable': False,
                'new': '',
                'prev': SongPerformer.READINESS_STRINGS[songperf.readiness],
                'value_translatable': True,
            })
        cls._song_changed(part.song, action, user, changes,
                          check_staffed=True, update_readiness=True)

    @classmethod
    def added_part(cls, user, song, old_parts):
        action = (ugettext_noop('%(who)s (f) added a song part %(when)s')
                  if user.profile.gender == 'f' else
                  ugettext_noop('%(who)s (m) added a song part %(when)s'))
        cls._parts_base(action, user, song, old_parts)

    @classmethod
    def removed_part(cls, user, song, old_parts):
        action = (ugettext_noop('%(who)s (f) removed a song part %(when)s')
                  if user.profile.gender == 'f' else
                  ugettext_noop('%(who)s (m) removed a song part %(when)s'))
        cls._parts_base(action, user, song, old_parts)

    @classmethod
    def _parts_base(cls, action, user, song, old_parts):
        new_parts = song.parts.all()
        changes = [
            {'title': ugettext_noop('Parts'),
             'title_translatable': True,
             'prev': '\n'.join(sorted(str(part) for part in old_parts)),
             'new': '\n'.join(sorted(str(part) for part in new_parts))}
        ]
        cls._song_changed(song, action, user, changes, check_staffed=True,
                          update_readiness=True)

    @classmethod
    def added_link(cls, user, song, old_links):
        action = (ugettext_noop('%(who)s (f) added a link %(when)s')
                  if user.profile.gender == 'f' else
                  ugettext_noop('%(who)s (m) added a song link %(when)s'))
        cls._links_base(action, user, song, old_links)

    @classmethod
    def removed_link(cls, user, song, old_links):
        action = (ugettext_noop('%(who)s (f) removed a link %(when)s')
                  if user.profile.gender == 'f' else
                  ugettext_noop('%(who)s (m) removed a link %(when)s'))
        cls._links_base(action, user, song, old_links)

    @classmethod
    def edited_link(cls, user, song, old_links):
        action = (ugettext_noop('%(who)s (f) edited a link %(when)s')
                  if user.profile.gender == 'f' else
                  ugettext_noop('%(who)s (m) edited a link %(when)s'))
        cls._links_base(action, user, song, old_links)

    @classmethod
    def _links_base(cls, action, user, song, old_links):
        new_links = song.links.all()
        changes = [
            {'title': ugettext_noop('Links'),
             'title_translatable': True,
             'prev': '\n'.join(sorted(str(link) for link in old_links)),
             'new': '\n'.join(sorted(str(link) for link in new_links))}
        ]
        cls._song_changed(song, action, user, changes)

    @classmethod
    def removed_from_gig(cls, user, song, old_gig):
        changes = [
            {'title': ugettext_noop('Gig'),
             'title_translatable': True,
             'prev': str(old_gig),
             'new': ''}
        ]
        action = (ugettext_noop('%(who)s (f) removed song from gig %(when)s')
                  if user.profile.gender == 'f' else
                  ugettext_noop('%(who)s (m) removed song from gig %(when)s'))
        info = {'action': action, 'changes': changes}
        sbgig.models.Comment.objects.create(
            gig=old_gig, song=song, author=user, text=json.dumps(info),
            comment_type=sbgig.models.Comment.CT_SONG_EDIT,
        )

    @classmethod
    def edited_song(cls, user, song):
        changes = []
        track_changes_of = [
            ('title', ugettext_noop('Title')),
            ('artist', ugettext_noop('Artist')),
            ('description', ugettext_noop('Description')),
        ]
        for field, verbose_name in track_changes_of:
            oldval = str(song._pristine[field] or '')
            newval = str(getattr(song, field))
            changes.append({
                'title': verbose_name,
                'title_translatable': True,
                'prev': oldval,
                'new': newval
            })
        action = (ugettext_noop('%(who)s (f) edited song %(when)s')
                  if user.profile.gender == 'f' else
                  ugettext_noop('%(who)s (m) edited song %(when)s'))
        cls._song_changed(song, action, user, changes)

    @classmethod
    def _song_changed(cls, song, action, user, changes, *,
                      check_staffed=False, update_readiness=False):
        if check_staffed:
            changes = cls._check_staffed(song, changes)
        if update_readiness:
            cls._update_readiness(song)
        changes = [
            change
            for change in changes
            if change['prev'] != change['new']
        ]
        if not changes:
            return
        info = {'action': action, 'changes': changes}
        sbgig.models.Comment.objects.create(
            gig=song.gig, song=song, author=user, text=json.dumps(info),
            comment_type=sbgig.models.Comment.CT_SONG_EDIT,
        )

    @classmethod
    def _check_staffed(cls, song, changes):
        new_staffed = False
        parts = song.parts.filter(required=True)
        if parts.exists():
            new_staffed = not (
                parts.annotate(num_perf=models.Count('songperformer'))
                     .filter(num_perf=0).exists()
            )
            new_changes = changes
        if song.staffed != new_staffed:
            bools_txt = {True: ugettext_noop('Yes'),
                         False: ugettext_noop('No')}
            new_changes = changes[:]
            new_changes.append(
                {'title': ugettext_noop('Song staffed'),
                 'title_translatable': True,
                 'prev': bools_txt[song.staffed],
                 'new': bools_txt[new_staffed],
                 'value_translatable': True}
            )
            song.staffed = new_staffed
            song.save()
        return new_changes

    @classmethod
    def _update_readiness(cls, song):
        parts_qs = song.parts.filter(required=True)
        num_parts = parts_qs.count()
        if num_parts == 0:
            new_readiness = 0
        else:
            all_readiness = parts_qs.annotate(
                best_perf=models.Max('songperformer__readiness')
            ).values_list('best_perf', flat=True)
            new_readiness = int(sum(r for r in all_readiness if r) / num_parts)
        if song.readiness == new_readiness:
            return
        song.readiness = new_readiness
        song.save()
