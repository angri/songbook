from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from sbsong import forms
from sbsong import models
import sbgig.models


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
            models.SongActions.suggested_song(request.user, new_song)
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
    empty_join_form = forms.JoinSongPartForm()

    all_parts = {part.pk: {'part': part,
                           'performers': [],
                           'join_form': empty_join_form,
                           'has_joined': False}
                 for part in song.parts.select_related('instrument')}
    all_performers = models.SongPerformer.objects.filter(part__song=song_id)
    all_performers = all_performers.select_related('part', 'part__instrument',
                                                   'performer')
    for part_perf in all_performers:
        all_parts[part_perf.part.pk]['performers'].append(part_perf)
        if part_perf.performer == request.user:
            all_parts[part_perf.part.pk]['has_joined'] = True
            all_parts[part_perf.part.pk]['join_form'] = forms.JoinSongPartForm(
                instance=part_perf
            )
    all_parts = [part_info for part_pk, part_info in sorted(all_parts.items())]

    all_links = [
        (link, forms.SongLinkForm(instance=link))
        for link in song.links.all()
    ]

    comments = song.comments.all()[:settings.SB_COMMENTS_ON_PAGE + 1]

    return render(request, 'sbsong/view_song.html',
                  {'song': song,
                   'parts': all_parts,
                   'links': all_links,
                   'new_part_form': new_part_form,
                   'new_link_form': new_link_form,
                   'comments': comments})


@login_required
def edit_song(request, song_id):
    song = get_object_or_404(models.Song, pk=song_id)
    if song.gig is None:
        return HttpResponse(status=403)
    form = forms.SongForm(request.POST or None, instance=song)
    if form.is_valid():
        form.save()
        models.SongActions.edited_song(request.user, song)
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
    models.SongActions.removed_from_gig(request.user, song, old_gig)
    messages.add_message(request, messages.INFO,
                         _('Song successfully removed'))
    return HttpResponseRedirect(reverse('sbgig:view-gig',
                                        args=[old_gig.slug]))


@login_required
def join_song_part(request, part_id):
    join_part_form = forms.JoinSongPartForm(request.POST)
    if join_part_form.is_valid():
        old_performers = list(
            models.SongPerformer.objects.filter(part_id=part_id)
        )
        songperf, created = models.SongPerformer.objects.update_or_create(
            part_id=part_id, performer=request.user,
            defaults=join_part_form.cleaned_data
        )
        if created:
            models.SongActions.joined_part(request.user, songperf.part,
                                           old_performers)
        else:
            models.SongActions.edited_part_participation(
                request.user, songperf.part, old_performers
            )
    return JsonResponse({'result': 'ok'})


@login_required
def leave_song_part(request, part_id):
    try:
        songperf = models.SongPerformer.objects.get(
            part_id=part_id, performer=request.user
        )
    except models.SongPerformer.DoesNotExist:
        pass
    else:
        part = songperf.part
        old_performers = list(part.songperformer_set.all())
        songperf.delete()
        models.SongActions.left_part(request.user, part, old_performers)
    return JsonResponse({'result': 'ok'})


@login_required
def add_song_part(request, song_id):
    form = forms.SongPartForm(request.POST)
    if form.is_valid():
        old_parts = list(models.SongPart.objects.filter(song_id=song_id))
        new_part = form.save(commit=False)
        new_part.song_id = song_id
        new_part.save()
        models.SongActions.added_part(request.user, new_part.song, old_parts)
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
        models.SongActions.removed_part(request.user, song, old_parts)
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
        models.SongActions.added_link(request.user, new_link.song, old_links)
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
        models.SongActions.removed_link(request.user, song, old_links)
    return JsonResponse({'result': 'ok'})


@login_required
def edit_song_link(request, link_id):
    link = get_object_or_404(models.SongLink, pk=link_id)
    form = forms.SongLinkForm(request.POST, instance=link)
    if form.is_valid():
        old_links = list(models.SongLink.objects.filter(song=link.song))
        form.save()
        models.SongActions.edited_link(request.user, link.song, old_links)
    return JsonResponse({'result': 'ok'})
