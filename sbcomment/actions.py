import json
from datetime import timedelta
from collections import OrderedDict

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.translation import ugettext_noop as _

import sbcomment.models
import sbsong.models


def suggested_song(user, song):
    action = (_('%(who)s (f) suggested a song %(when)s')
              if user.profile.gender == 'f' else
              _('%(who)s (m) suggested a song %(when)s'))
    changes = [
        {'title': _('Artist'),
         'title_translatable': True,
         'prev': '',
         'new': song.artist},
        {'title': _('Title'),
         'title_translatable': True,
         'prev': '',
         'new': song.title},
        {'title': _('Description'),
         'title_translatable': True,
         'prev': '',
         'new': song.description},
    ]
    _song_changed(song, action, user, changes)
    sbsong.models.SongWatcher.objects.update_or_create(song=song, user=user)


def joined_part(user, part, old_performers, *, changed_by=None):
    sbsong.models.SongWatcher.objects.update_or_create(song=part.song,
                                                       user=user)
    action = (_('%(who)s (f) joined a song part %(when)s')
              if user.profile.gender == 'f' else
              _('%(who)s (m) joined a song part %(when)s'))
    return _part_participation_base(action, user, part, old_performers,
                                    changed_by=changed_by)


def edited_part_participation(user, part, old_performers):
    action = (
        _('%(who)s (f) edited part participation %(when)s')
        if user.profile.gender == 'f' else
        _('%(who)s (m) edited part participation %(when)s')
    )
    return _part_participation_base(action, user, part, old_performers)


def left_part(user, part, old_performers, changed_by):
    action = (_('%(who)s (f) left a song part %(when)s')
              if user.profile.gender == 'f' else
              _('%(who)s (m) left a song part %(when)s'))
    return _part_participation_base(action, user, part, old_performers,
                                    changed_by=changed_by)


def _part_participation_base(action, user, part, old_performers,
                             changed_by=None):
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
    readiness_strings = sbsong.models.SongPerformer.READINESS_STRINGS
    for songperf in new_performers:
        old_performer = old_performers_by_id.pop(songperf.id, None)
        old_readiness = (readiness_strings[old_performer.readiness]
                         if old_performer is not None
                         else '')
        changes.append({
            'title': "%s / %s" % (songperf, songperf.part),
            'title_translatable': False,
            'prev': old_readiness,
            'new': readiness_strings[songperf.readiness],
            'value_translatable': True,
        })
    for sp_id, songperf in sorted(old_performers_by_id.items()):
        changes.append({
            'title': "%s / %s" % (songperf, songperf.part),
            'title_translatable': False,
            'new': '',
            'prev': readiness_strings[songperf.readiness],
            'value_translatable': True,
        })
    _song_changed(part.song, action, user, changes,
                  check_staffed=True, update_readiness=True,
                  changed_by=changed_by)


def added_part(user, song, old_parts):
    action = (_('%(who)s (f) added a song part %(when)s')
              if user.profile.gender == 'f' else
              _('%(who)s (m) added a song part %(when)s'))
    _parts_base(action, user, song, old_parts)


def removed_part(user, song, old_parts):
    action = (_('%(who)s (f) removed a song part %(when)s')
              if user.profile.gender == 'f' else
              _('%(who)s (m) removed a song part %(when)s'))
    _parts_base(action, user, song, old_parts)


def _parts_base(action, user, song, old_parts):
    new_parts = song.parts.all()
    changes = [
        {'title': _('Parts'),
         'title_translatable': True,
         'prev': '\n'.join(sorted(str(part) for part in old_parts)),
         'new': '\n'.join(sorted(str(part) for part in new_parts))}
    ]
    _song_changed(song, action, user, changes, check_staffed=True,
                  update_readiness=True)


def added_link(user, song, old_links):
    action = (_('%(who)s (f) added a link %(when)s')
              if user.profile.gender == 'f' else
              _('%(who)s (m) added a song link %(when)s'))
    _links_base(action, user, song, old_links)


def removed_link(user, song, old_links):
    action = (_('%(who)s (f) removed a link %(when)s')
              if user.profile.gender == 'f' else
              _('%(who)s (m) removed a link %(when)s'))
    _links_base(action, user, song, old_links)


def edited_link(user, song, old_links):
    action = (_('%(who)s (f) edited a link %(when)s')
              if user.profile.gender == 'f' else
              _('%(who)s (m) edited a link %(when)s'))
    _links_base(action, user, song, old_links)


def _links_base(action, user, song, old_links):
    new_links = song.links.all()
    changes = [
        {'title': _('Links'),
         'title_translatable': True,
         'prev': '\n'.join(sorted(str(link) for link in old_links)),
         'new': '\n'.join(sorted(str(link) for link in new_links))}
    ]
    _song_changed(song, action, user, changes)


def removed_from_gig(user, song, old_gig):
    changes = [
        {'title': _('Gig'),
         'title_translatable': True,
         'prev': str(old_gig),
         'new': ''}
    ]
    action = (_('%(who)s (f) removed song from gig %(when)s')
              if user.profile.gender == 'f' else
              _('%(who)s (m) removed song from gig %(when)s'))
    _song_changed(song, action, user, changes, override_gig=old_gig)


def edited_song(user, song):
    changes = []
    track_changes_of = [
        ('title', _('Title')),
        ('artist', _('Artist')),
        ('description', _('Description')),
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
    action = (_('%(who)s (f) edited song %(when)s')
              if user.profile.gender == 'f' else
              _('%(who)s (m) edited song %(when)s'))
    _song_changed(song, action, user, changes)


def song_comment_written(song, user, text):
    sbcomment.models.Comment.objects.create(
        gig=song.gig, song=song, author=user,
        text=text, comment_type=sbcomment.models.Comment.CT_SONG_COMMENT
    )
    _update_changed_at(song, user)


def song_copied(user, song, prev_gig, prev_song_id):
    changes = [
        {'title': _('Gig'),
         'title_translatable': True,
         'prev': str(prev_gig),
         'new': str(song.gig)},
        {'title': _('Song id'),
         'title_translatable': True,
         'prev': str(prev_song_id),
         'new': str(song.id)},
    ]
    action = (_('%(who)s (f) copied song %(when)s')
              if user.profile.gender == 'f' else
              _('%(who)s (m) copied song %(when)s'))
    _song_changed(song, action, user, changes,
                  check_staffed=True, update_readiness=True)


def _song_changed(song, action, user, changes, *,
                  check_staffed=False, update_readiness=False,
                  override_gig=None, changed_by=None):
    if check_staffed:
        changes = _check_staffed(song, changes)
    if update_readiness:
        _update_readiness(song)
    changes = [
        change
        for change in changes
        if change['prev'] != change['new']
    ]
    if not changes:
        return
    info = {'action': action, 'changes': changes}
    if changed_by is not None and changed_by != user:
        info['changed_by'] = str(changed_by)

    gig = override_gig or song.gig
    _create_or_update_comment(
        gig=gig, song=song, author=user, info=info,
        comment_type=sbcomment.models.Comment.CT_SONG_EDIT
    )
    _update_changed_at(song, changed_by or user)


def _create_or_update_comment(gig, song, author, info, comment_type):
    min_datetime = (timezone.now()
                    - timedelta(seconds=settings.SB_UPDATE_COMMENT_GAP))
    last_comment = sbcomment.models.Comment.objects.filter(
        datetime__gt=min_datetime
    ).order_by('-datetime').first()
    if (last_comment is not None
            and last_comment.author == author
            and last_comment.gig == gig
            and last_comment.song == song
            and last_comment.comment_type == comment_type):
        prev_info = json.loads(last_comment.text)
        if prev_info['action'] == info['action']:
            changes = _merge_changes(prev_info['changes'], info['changes'])
            if not changes:
                last_comment.delete()
            else:
                info['changes'] = changes
                last_comment.text = json.dumps(info)
                last_comment.save()
            return

    sbcomment.models.Comment.objects.create(
        gig=gig, song=song, author=author, comment_type=comment_type,
        text=json.dumps(info)
    )


def _merge_changes(old_changes, new_changes):
    merged = []
    new_changes = OrderedDict(
        ((change['title'], change['title_translatable']), change)
        for change in new_changes
    )
    for change in old_changes:
        key = (change['title'], change['title_translatable'])
        new_change = new_changes.pop(key, None)
        if new_change is None:
            merged.append(change)
            continue
        change['new'] = new_change['new']
        if change['prev'] != change['new']:
            merged.append(change)
    for change in new_changes.values():
        merged.append(change)
    return merged


def _update_changed_at(song, user):
    now = timezone.now()
    sbsong.models.SongWatcher.objects.filter(
        song=song, user=user, last_seen__gte=song.changed_at
    ).update(last_seen=now)
    song.changed_at = now
    song.changed_by = user
    song.save()


def _check_staffed(song, changes):
    new_staffed = False
    parts = song.parts.filter(required=True)
    new_changes = changes
    if parts.exists():
        new_staffed = not (
            parts.annotate(num_perf=models.Count('songperformer'))
                 .filter(num_perf=0).exists()
        )
    if song.staffed != new_staffed:
        bools_txt = {True: _('Yes'),
                     False: _('No')}
        new_changes = changes[:]
        new_changes.append(
            {'title': _('Song staffed'),
             'title_translatable': True,
             'prev': bools_txt[song.staffed],
             'new': bools_txt[new_staffed],
             'value_translatable': True}
        )
        song.staffed = new_staffed
        song.save()
    return new_changes


def _update_readiness(song):
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


def edited_gig(user, gig):
    changes = []
    track_changes_of = [
        ('title', _('Gig name')),
        ('date', _('Gig date')),
        ('description', _('Description')),
    ]
    for field, verbose_name in track_changes_of:
        oldval = str(gig._pristine[field] or '')
        newval = str(getattr(gig, field))
        if oldval != newval:
            changes.append({
                'title': verbose_name,
                'title_translatable': True,
                'prev': oldval,
                'new': newval
            })
    if not changes:
        return
    action = (_('%(who)s (f) edited gig %(when)s')
              if user.profile.gender == 'f' else
              _('%(who)s (m) edited gig %(when)s'))
    info = {'action': action, 'changes': changes}
    sbcomment.models.Comment.objects.create(
        gig=gig, song=None, author=user,
        text=json.dumps(info),
        comment_type=sbcomment.models.Comment.CT_GIG_EDIT,
    )
