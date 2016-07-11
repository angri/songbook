from collections import defaultdict
import itertools

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Count
from django.conf import settings

import sbsong.models
import sbgig.models
import sbgig.forms


@login_required
def view_gig(request, slug):
    gig = get_object_or_404(sbgig.models.Gig, slug=slug)
    staffed_songs = list(gig.songs.filter(staffed=True))
    unstaffed_songs = list(gig.songs.filter(staffed=False))
    empty_parts = (sbsong.models.SongPart.objects.filter(song__gig=gig)
                         .annotate(num_perf=Count('songperformer'))
                         .filter(num_perf=0)
                         .select_related('instrument')
                         .order_by('song', 'id'))
    empty_parts_by_song_id = defaultdict(list)
    songwatchers = sbsong.models.SongWatcher.objects.filter(user=request.user,
                                                            song__gig=gig)
    mine_song_ids = set(
        gig.songs.filter(parts__songperformer__performer=request.user)
                 .values_list('pk', flat=True)
    )
    songwatchers = dict(songwatchers.values_list('song_id', 'last_seen'))
    songs = {
        'staffed-mine': [],
        'staffed-other': [],
        'unstaffed-mine': [],
        'unstaffed-other': [],
    }
    for song in itertools.chain(staffed_songs, unstaffed_songs):
        last_seen = songwatchers.get(song.id)
        song.is_watched = last_seen is not None
        song.updated_since_last_seen = None
        if song.is_watched:
            song.updated_since_last_seen = (song.changed_at > last_seen)
        song.is_mine = song.id in mine_song_ids
    for empty_part in empty_parts:
        empty_parts_by_song_id[empty_part.song_id].append(empty_part)
    for song in unstaffed_songs:
        song.unstaffed_parts = empty_parts_by_song_id.get(song.id, ())
        if song.is_mine:
            songs['unstaffed-mine'].append(song)
        else:
            songs['unstaffed-other'].append(song)
    for song in staffed_songs:
        song.desirable_parts = empty_parts_by_song_id.get(song.id, ())
        if song.is_mine:
            songs['staffed-mine'].append(song)
        else:
            songs['staffed-other'].append(song)
    comments = gig.comments.filter(
        comment_type__in=sbgig.models.Comment.GIG_ONLY_COMMENTS
    )[:settings.SB_COMMENTS_ON_PAGE + 1]
    user_plays = set(request.user.plays.all().values_list('instrument_id',
                                                          flat=True))
    return render(request, 'sbgig/view_gig.html',
                  {'gig': gig, 'songs': songs,
                   'comments': comments, 'user_plays': user_plays})


@login_required
def edit_gig(request, slug):
    gig = get_object_or_404(sbgig.models.Gig, slug=slug)
    form = sbgig.forms.GigForm(request.POST or None, instance=gig)
    if form.is_valid():
        form.save()
        gig.track_changes(request.user)
        messages.add_message(request, messages.INFO,
                             _("Gig successfully saved"))
        return HttpResponseRedirect(reverse('sbgig:view-gig', args=[slug]))
    return render(request, 'sbgig/edit_gig.html',
                  {'gig': gig, 'form': form})


@login_required
def add_gig_comment(request, slug):
    gig = get_object_or_404(sbgig.models.Gig, slug=slug)
    text = request.POST.get('body').strip()
    if not text:
        return HttpResponse(status=400)
    sbgig.models.Comment.objects.create(
        gig=gig, author=request.user,
        text=text, comment_type=sbgig.models.Comment.CT_GIG_COMMENT
    )
    return JsonResponse({'result': 'ok'})


@login_required
def add_song_comment(request, song_id):
    song = get_object_or_404(sbsong.models.Song, pk=song_id)
    text = request.POST.get('body').strip()
    if not text:
        return HttpResponse(status=400)
    sbsong.models.SongActions.song_comment_written(song, request.user, text)
    return JsonResponse({'result': 'ok'})


def _get_comments(request, gig, song):
    not_after = request.GET.get('not_after')
    not_before = request.GET.get('not_before')
    if song:
        qs = song.comments.all()
    else:
        qs = gig.comments.all()
    if not_before:
        qs = qs.filter(id__gt=not_before)
    if not_after:
        qs = qs.filter(id__lt=not_after)
    if song is None:
        qs = qs.filter(comment_type__in=sbgig.models.Comment.GIG_ONLY_COMMENTS)
    qs = qs.select_related('song', 'gig', 'author')
    comments = list(qs[:settings.SB_COMMENTS_ON_PAGE + 1])
    songwatcher = None
    if song:
        songwatcher = song.watchers.filter(user=request.user).first()
    return render(request, 'sbgig/comments.html', {'comments': comments,
                                                   'songwatcher': songwatcher})


@login_required
def get_gig_comments(request, slug):
    gig = get_object_or_404(sbgig.models.Gig, slug=slug)
    return _get_comments(request, gig, song=None)


@login_required
def get_song_comments(request, song_id):
    song = get_object_or_404(sbsong.models.Song, pk=song_id)
    return _get_comments(request, song.gig, song)


@login_required
def setlist(request, slug):
    gig = get_object_or_404(sbgig.models.Gig, slug=slug)
    songs = list(gig.songs.filter(staffed=True))
    song_ids = [song.id for song in songs]
    songperfs = sbsong.models.SongPerformer.objects.filter(
        part__song__pk__in=song_ids
    ).select_related(
        'part__song', 'performer', 'part__instrument'
    )
    performer_by_song_by_instrument = defaultdict(lambda: defaultdict(list))
    used_instruments = set()
    for songperf in songperfs:
        used_instruments.add(songperf.part.instrument)
        songparts = performer_by_song_by_instrument[songperf.part.song]
        songparts[songperf.part.instrument].append(songperf.performer)
    used_instruments = sorted(used_instruments,
                              key=lambda instrument: instrument.name)
    return render(
        request, 'sbgig/setlist.html',
        {'gig': gig, 'used_instruments': used_instruments, 'songs': songs,
         'performer_by_song_by_instrument': performer_by_song_by_instrument}
    )
