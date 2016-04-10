from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required

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
            models.SongWatcher.objects.create(song=new_song,
                                              user=request.user).save()
            return HttpResponseRedirect('/thanks/')
    else:
        form = forms.SongForm()
    return render(request, 'sb/suggest_a_song.html', {'form': form})


@login_required
def view_song(request, song_id):
    song = get_object_or_404(models.Song, pk=song_id)
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

    new_part_form = forms.SongPartForm()

    all_parts = [part_info for part_pk, part_info in sorted(all_parts.items())]
    return render(request, 'sb/view_song.html',
                  {'song': song, 'parts': all_parts,
                   'new_part_form': new_part_form})


@login_required
def join_song_part(request, part_id):
    join_part_form = forms.JoinSongPartForm(request.POST)
    if join_part_form.is_valid():
        songperf, created = models.SongPerformer.objects.update_or_create(
            part_id=part_id, performer=request.user,
            defaults={'notice': join_part_form.cleaned_data['notice']}
        )
    return JsonResponse({'result': 'ok'})


@login_required
def leave_song_part(request, part_id):
    try:
        songperf = models.SongPerformer.objects.get(
            part_id=part_id, performer=request.user
        )
        songperf.delete()
    except models.SongPerformer.DoesNotExist:
        pass
    return JsonResponse({'result': 'ok'})


@login_required
def add_song_part(request, song_id):
    form = forms.SongPartForm(request.POST)
    if form.is_valid():
        models.SongPart.objects.create(
            song_id=song_id,
            notice=form.cleaned_data['notice'],
            instrument=form.cleaned_data['instrument']
        )
    else:
        print(form.errors)
    return JsonResponse({'result': 'ok'})


@login_required
def remove_song_part(request, part_id):
    try:
        part = models.SongPart.objects.get(pk=part_id)
        part.delete()
    except models.SongPerformer.DoesNotExist:
        pass
    return JsonResponse({'result': 'ok'})
