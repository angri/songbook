import json

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop


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
    title = models.CharField(max_length=150, null=False, blank=False)
    artist = models.CharField(max_length=100, null=False, blank=True)
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
                             null=False, blank=False, related_name='links')
    link = models.URLField(null=False, blank=False)
    notice = models.CharField(max_length=150, null=False, blank=True)

    class Meta:
        unique_together = [
            ('song', 'link'),
        ]

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
                                   null=False, blank=False)
    notice = models.CharField(max_length=200, null=False, blank=True)

    def __str__(self):
        if self.notice:
            return "%s (%s)" % (self.instrument.name, self.notice)
        else:
            return self.instrument.name


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

    def __str__(self):
        if self.notice:
            return "%s (%s)" % (self.performer.username, self.notice)
        else:
            return self.performer.username


class SongComment(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE,
                             blank=False, null=False, related_name='comments')
    comment_type = models.CharField(max_length=20, null=False, blank=False,
                                    choices=[('regular', 'regular comment'),
                                             ('song_changed', 'song edit')],
                                    default='regular')
    author = models.ForeignKey(User, on_delete=models.PROTECT,
                               null=True, blank=True)
    datetime = models.DateTimeField(auto_now_add=True)
    text = models.TextField(null=False, blank=False)

    class Meta:
        ordering = ['song', '-datetime']


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
        cls._song_changed(part.song, action, user, changes)

    @classmethod
    def added_part(cls, user, song, old_parts):
        action = (ugettext_noop('%(who) (f) added a song part %(when)s')
                  if user.profile.gender == 'f' else
                  ugettext_noop('%(who) (m) added a song part %(when)s'))
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
        cls._song_changed(song, action, user, changes)

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
    def _song_changed(cls, song, action, user, changes):
        changes = [
            change
            for change in changes
            if change['prev'] != change['new']
        ]
        if not changes:
            return
        info = {'action': action, 'changes': changes}
        SongComment.objects.create(song=song, comment_type='song_changed',
                                   author=user, text=json.dumps(info))
