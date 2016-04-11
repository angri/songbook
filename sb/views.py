from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_noop
from django.core.urlresolvers import reverse

from sb import forms
from sb import models


@login_required
def index(request):
    return HttpResponse("Hello, world. You're at the sb index.")


@login_required
def suggest_a_song(request):
    if request.method == 'POST':
        form = forms.SongForm(request.POST)
        if form.is_valid():
            new_song = form.save(commit=False)
            new_song.suggested_by = request.user
            new_song.changed_by = request.user
            new_song.save()
            changes = {
                ugettext_noop('Artist'): ('', new_song.artist),
                ugettext_noop('Title'): ('', new_song.title),
                ugettext_noop('Description'): ('', new_song.description)
            }
            models.song_changed(new_song, ugettext_noop('Suggested a song'),
                                request.user, changes)
            models.SongWatcher.objects.create(song=new_song,
                                              user=request.user).save()
            return HttpResponseRedirect(reverse('sb:view_song',
                                                args=[new_song.pk]))
    else:
        form = forms.SongForm()
    return render(request, 'sb/suggest_a_song.html', {'form': form})


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
                 for part in song.parts.all()}
    all_performers = models.SongPerformer.objects.filter(part__song=song_id)
    for part_perf in all_performers:
        all_parts[part_perf.part.pk]['performers'].append(part_perf)
        if part_perf.performer == request.user:
            all_parts[part_perf.part.pk]['has_joined'] = True
            all_parts[part_perf.part.pk]['join_form'] = forms.JoinSongPartForm(
                initial={'notice': part_perf.notice}
            )
    all_parts = [part_info for part_pk, part_info in sorted(all_parts.items())]

    all_links = [
        (link, forms.SongLinkForm(instance=link))
        for link in song.songlink_set.all()
    ]

    return render(request, 'sb/view_song.html',
                  {'song': song,
                   'parts': all_parts,
                   'links': all_links,
                   'new_part_form': new_part_form,
                   'new_link_form': new_link_form})


@login_required
def join_song_part(request, part_id):
    join_part_form = forms.JoinSongPartForm(request.POST)
    if join_part_form.is_valid():
        old_performers = list(
            models.SongPerformer.objects.filter(part_id=part_id)
        )
        songperf, created = models.SongPerformer.objects.update_or_create(
            part_id=part_id, performer=request.user,
            defaults={'notice': join_part_form.cleaned_data['notice']}
        )
        new_performers = songperf.part.songperformer_set.all()
        changes = {
            str(songperf.part): (
                sorted(str(songperformer)
                       for songperformer in old_performers),
                sorted(str(songperformer)
                       for songperformer in new_performers)
            )
        }
        models.song_changed(
            songperf.part.song,
            ugettext_noop('Joined a part')
            if created
            else ugettext_noop('Edited part participation notice'),
            request.user, changes)
    return JsonResponse({'result': 'ok'})


@login_required
def leave_song_part(request, part_id):
    try:
        songperf = models.SongPerformer.objects.get(
            part_id=part_id, performer=request.user
        )
        part = songperf.part
        old_performers = list(part.songperformer_set.all())
        songperf.delete()
        changes = {
            str(part): (
                sorted(str(songperformer)
                       for songperformer in old_performers),
                sorted(str(songperformer)
                       for songperformer in old_performers
                       if songperformer.performer != request.user)
            )
        }
        models.song_changed(songperf.part.song,
                            ugettext_noop('Left a part'),
                            request.user, changes)
    except models.SongPerformer.DoesNotExist:
        pass
    return JsonResponse({'result': 'ok'})


@login_required
def add_song_part(request, song_id):
    form = forms.SongPartForm(request.POST)
    if form.is_valid():
        new_part = models.SongPart.objects.create(
            song_id=song_id,
            notice=form.cleaned_data['notice'],
            instrument=form.cleaned_data['instrument']
        )
        changes = {
            ugettext_noop('Parts'): (
                sorted(str(part)
                       for part in new_part.song.parts.all()
                       if part != new_part),
                sorted(str(part) for part in new_part.song.parts.all())
            )
        }
        models.song_changed(new_part.song,
                            ugettext_noop('Added a part'),
                            request.user, changes)
    return JsonResponse({'result': 'ok'})


@login_required
def remove_song_part(request, part_id):
    try:
        removed_part = models.SongPart.objects.get(pk=part_id)
        song = removed_part.song
        old_parts = list(song.parts.all())
        removed_part.delete()
        changes = {
            ugettext_noop('Parts'): (
                sorted(str(part) for part in old_parts),
                sorted(str(part) for part in song.parts.all())
            )
        }
        models.song_changed(song, ugettext_noop('Removed a part'),
                            request.user, changes)
    except models.SongPart.DoesNotExist:
        pass
    return JsonResponse({'result': 'ok'})


@login_required
def add_song_link(request, song_id):
    form = forms.SongLinkForm(request.POST)
    if form.is_valid():
        new_link = models.SongLink.objects.create(
            song_id=song_id,
            notice=form.cleaned_data['notice'],
            link=form.cleaned_data['link']
        )
        changes = {
            ugettext_noop('Links'): (
                sorted(str(link)
                       for link in new_link.song.songlink_set.all()
                       if link != new_link),
                sorted(str(link) for link in new_link.song.songlink_set.all())
            )
        }
        models.song_changed(new_link.song,
                            ugettext_noop('Added a link'),
                            request.user, changes)
    return JsonResponse({'result': 'ok'})


@login_required
def remove_song_link(request, link_id):
    try:
        link = models.SongLink.objects.get(pk=link_id)
        old_links = list(link.song.songlink_set.all())
        link.delete()
        changes = {
            ugettext_noop('Links'): (
                sorted(str(link) for link in old_links),
                sorted(str(link) for link in link.song.songlink_set.all())
            )
        }
        models.song_changed(link.song, ugettext_noop('Removed a link'),
                            request.user, changes)
    except models.SongLink.DoesNotExist:
        pass
    return JsonResponse({'result': 'ok'})


@login_required
def edit_song_link(request, link_id):
    link = get_object_or_404(models.SongLink, pk=link_id)
    form = forms.SongLinkForm(request.POST, instance=link)
    if form.is_valid():
        old_links = list(models.SongLink.objects.filter(song=link.song))
        form.save()
        changes = {
            ugettext_noop('Links'): (
                sorted(str(link) for link in old_links),
                sorted(str(link) for link in link.song.songlink_set.all())
            )
        }
        models.song_changed(link.song, ugettext_noop('Edited a link'),
                            request.user, changes)
    return JsonResponse({'result': 'ok'})
