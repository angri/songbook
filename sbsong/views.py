from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from sbsong import forms
from sbsong import models
import sbgig.models
import sbcomment.actions


@login_required
def suggest_a_song(request, gigslug):
    gig = get_object_or_404(sbgig.models.Gig, slug=gigslug)
    if request.method == 'POST':
        form = forms.SongForm(request.POST)
        if form.is_valid():
            new_song = form.save(commit=False)
            new_song.suggested_by = request.user
            new_song.changed_by = request.user
            new_song.gig = gig
            new_song.save()
            sbcomment.actions.suggested_song(request.user, new_song)
            return HttpResponseRedirect(reverse('sbsong:view-song',
                                                args=[new_song.pk]))
    else:
        form = forms.SongForm()
    return render(request, 'sbsong/suggest_a_song.html',
                  {'form': form, 'gig': gig})


@login_required
def view_song(request, song_id):
    song = get_object_or_404(models.Song, pk=song_id)

    new_part_form = forms.SongPartForm()
    new_link_form = forms.SongLinkForm()
    empty_join_form = forms.JoinSongPartFormWithPerformerSelect()

    all_parts = {part.pk: {'part': part,
                           'performers': [],
                           'has_joined': False}
                 for part in song.parts.select_related('instrument')}
    all_performers = models.SongPerformer.objects.filter(part__song=song_id)
    all_performers = all_performers.select_related('part', 'part__instrument',
                                                   'performer')
    for part_perf in all_performers:
        all_parts[part_perf.part.pk]['performers'].append(part_perf)
        if part_perf.performer == request.user:
            all_parts[part_perf.part.pk]['has_joined'] = True
            all_parts[part_perf.part.pk]['part_edit_form'] = \
                forms.JoinSongPartForm(instance=part_perf)
    all_parts = [part_info for part_pk, part_info in sorted(all_parts.items())]

    all_links = [
        (link, forms.SongLinkForm(instance=link))
        for link in song.links.all()
    ]

    songwatcher = song.watchers.filter(user=request.user).first()
    last_seen = None
    comments = song.comments.all()[:settings.SB_COMMENTS_ON_PAGE + 1]
    num_unread_comments = 0
    if songwatcher:
        num_unread_comments = song.comments.filter(
            datetime__gt=songwatcher.last_seen
        ).count()
        last_seen = songwatcher.last_seen
        songwatcher.last_seen = timezone.now()
        songwatcher.save()

    copy_to_gig_form = forms.make_copy_to_gig_form(exclude_gig=song.gig)

    return render(request, 'sbsong/view_song.html',
                  {'song': song,
                   'join_form': empty_join_form,
                   'parts': all_parts,
                   'links': all_links,
                   'new_part_form': new_part_form,
                   'new_link_form': new_link_form,
                   'comments': comments,
                   'songwatcher': songwatcher,
                   'last_seen': last_seen,
                   'num_unread_comments': num_unread_comments,
                   'copy_to_gig_form': copy_to_gig_form})


@login_required
def watch_unwatch_song(request, song_id):
    song = get_object_or_404(models.Song, pk=song_id)
    action = request.POST.get('action')
    if request.method != 'POST' or action not in ('watch', 'unwatch'):
        return HttpResponse(status=400)
    if action == 'watch':
        models.SongWatcher.objects.get_or_create(user=request.user, song=song)
    else:
        models.SongWatcher.objects.filter(user=request.user,
                                          song=song).delete()
    return JsonResponse({'result': 'ok'})


@login_required
def mark_song_as_seen(request, song_id):
    songwatcher = get_object_or_404(models.SongWatcher, song_id=song_id,
                                    user_id=request.user.id)
    songwatcher.last_seen = timezone.now()
    songwatcher.save()
    return JsonResponse({'result': 'ok'})


@login_required
def edit_song(request, song_id):
    song = get_object_or_404(models.Song, pk=song_id)
    if song.gig is None:
        return HttpResponse(status=403)
    form = forms.SongForm(request.POST or None, instance=song)
    if form.is_valid():
        form.save()
        sbcomment.actions.edited_song(request.user, song)
        return HttpResponseRedirect(reverse('sbsong:view-song',
                                            args=[song.pk]))
    return render(request, 'sbsong/edit_song.html',
                  {'form': form, 'song': song})


@login_required
def remove_song(request, song_id):
    song = get_object_or_404(models.Song, pk=song_id)
    old_gig = song.gig
    song.gig = None
    song.save()
    sbcomment.actions.removed_from_gig(request.user, song, old_gig)
    messages.add_message(request, messages.INFO,
                         _('Song successfully removed'))
    return HttpResponseRedirect(reverse('sbgig:view-gig',
                                        args=[old_gig.slug]))


@login_required
def join_song_part(request, part_id):
    if request.method == 'POST' and 'performer' in request.POST:
        form_cls = forms.JoinSongPartFormWithPerformerSelect
    else:
        form_cls = forms.JoinSongPartForm
    join_part_form = form_cls(request.POST)
    if join_part_form.is_valid():
        old_performers = list(
            models.SongPerformer.objects.filter(part_id=part_id)
        )
        performer = request.user
        if 'performer' in join_part_form.cleaned_data:
            performer = join_part_form.cleaned_data['performer']
        songperf, created = models.SongPerformer.objects.update_or_create(
            part_id=part_id, performer=performer,
            defaults=join_part_form.cleaned_data
        )
        if created:
            sbcomment.actions.joined_part(songperf.performer, songperf.part,
                                          old_performers,
                                          changed_by=request.user)
        else:
            sbcomment.actions.edited_part_participation(
                request.user, songperf.part, old_performers
            )
    return JsonResponse({'result': 'ok'})


@login_required
def kick_from_song_part(request, part_id, performer_id):
    try:
        songperf = models.SongPerformer.objects.get(
            part_id=part_id, performer=performer_id
        )
    except models.SongPerformer.DoesNotExist:
        pass
    else:
        part = songperf.part
        user = songperf.performer
        old_performers = list(part.songperformer_set.all())
        songperf.delete()
        sbcomment.actions.left_part(user, part, old_performers,
                                    changed_by=request.user)
    return JsonResponse({'result': 'ok'})


@login_required
def add_song_part(request, song_id):
    form = forms.SongPartForm(request.POST)
    if form.is_valid():
        old_parts = list(models.SongPart.objects.filter(song_id=song_id))
        new_part = form.save(commit=False)
        new_part.song_id = song_id
        new_part.save()
        sbcomment.actions.added_part(request.user, new_part.song, old_parts)
    return JsonResponse({'result': 'ok'})


@login_required
def remove_song_part(request, part_id):
    try:
        removed_part = models.SongPart.objects.get(pk=part_id)
    except models.SongPart.DoesNotExist:
        pass
    else:
        song = removed_part.song
        old_parts = list(song.parts.all())
        removed_part.delete()
        sbcomment.actions.removed_part(request.user, song, old_parts)
    return JsonResponse({'result': 'ok'})


@login_required
def add_song_link(request, song_id):
    form = forms.SongLinkForm(request.POST)
    if form.is_valid():
        old_links = list(models.SongLink.objects.filter(song_id=song_id))
        new_link = models.SongLink.objects.create(
            song_id=song_id,
            notice=form.cleaned_data['notice'],
            link=form.cleaned_data['link']
        )
        sbcomment.actions.added_link(request.user, new_link.song, old_links)
    return JsonResponse({'result': 'ok'})


@login_required
def remove_song_link(request, link_id):
    try:
        link = models.SongLink.objects.get(pk=link_id)
    except models.SongLink.DoesNotExist:
        pass
    else:
        old_links = list(link.song.links.all())
        song = link.song
        link.delete()
        sbcomment.actions.removed_link(request.user, song, old_links)
    return JsonResponse({'result': 'ok'})


@login_required
def edit_song_link(request, link_id):
    link = get_object_or_404(models.SongLink, pk=link_id)
    form = forms.SongLinkForm(request.POST, instance=link)
    if form.is_valid():
        old_links = list(models.SongLink.objects.filter(song=link.song))
        form.save()
        sbcomment.actions.edited_link(request.user, link.song, old_links)
    return JsonResponse({'result': 'ok'})


@login_required
def copy_song(request, song_id):
    song = get_object_or_404(models.Song, pk=song_id)
    form = forms.make_copy_to_gig_form(request.POST or None,
                                       exclude_gig=song.gig)
    if not form or not form.is_valid():
        return HttpResponse(status=400)
    gig = get_object_or_404(sbgig.models.Gig,
                            id=form.cleaned_data['target_gig'])
    if gig == song.gig:
        return HttpResponse(status=400)

    parts = {part.id: part for part in song.parts.all()}
    links = list(song.links.all())
    songperfs = list(models.SongPerformer.objects.filter(part__song=song))
    watchers = list(song.watchers.all())

    song.pk = None
    prev_gig = song.gig
    song.gig = gig
    song.suggested_by = request.user
    song.save()

    for part in parts.values():
        part.pk = None
        part.song = song
        part.save()

    for watcher in watchers:
        watcher.pk = None
        watcher.song = song
        watcher.save()

    if form.cleaned_data['copy_participants']:
        for perf in songperfs:
            perf.part = parts[perf.part_id]
            perf.pk = None
            perf.save()

    if form.cleaned_data['copy_links']:
        for link in links:
            link.pk = None
            link.song = song
            link.save()

    sbcomment.actions.song_copied(request.user, song, prev_gig, song_id)

    return HttpResponseRedirect(reverse('sbsong:view-song',
                                        args=[song.pk]))
