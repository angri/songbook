from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse

from sb import forms
from sb import models


def index(request):
    return HttpResponse("Hello, world. You're at the sb index.")


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

    all_parts = [part_info for part_pk, part_info in sorted(all_parts.items())]
    return render(request, 'sb/view_song.html',
                  {'song': song, 'parts': all_parts})


def join_song_part(request, part_id):
    join_part_form = forms.JoinSongPartForm(request.POST)
    if join_part_form.is_valid():
        songperf, created = models.SongPerformer.objects.update_or_create(
            part_id=part_id, performer=request.user,
            defaults={'notice': join_part_form.cleaned_data['notice']}
        )
    return JsonResponse({'result': 'ok'})
