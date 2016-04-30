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
    for song in unstaffed_songs:
        song.unstaffed_parts = (
            song.parts.filter(required=True)
                      .annotate(num_perf=Count('songperformer'))
                      .filter(num_perf=0)
                      .select_related('instrument')
        )
    comments = gig.comments.all()[:settings.SB_COMMENTS_ON_PAGE + 1]
    return render(request, 'sbgig/view_gig.html',
                  {'gig': gig, 'unstaffed_songs': unstaffed_songs,
                   'staffed_songs': staffed_songs,
                   'comments': comments})


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


def _add_comment(request, gig, song):
    text = request.POST.get('body').strip()
    if not text:
        return HttpResponse(status=400)
    comment_type = sbgig.models.Comment.CT_GIG_COMMENT
    if song is not None:
        comment_type = sbgig.models.Comment.CT_SONG_COMMENT
    sbgig.models.Comment.objects.create(
        gig=gig, song=song, author=request.user,
        text=text, comment_type=comment_type
    )
    return JsonResponse({'result': 'ok'})


@login_required
def add_gig_comment(request, slug):
    gig = get_object_or_404(sbgig.models.Gig, slug=slug)
    return _add_comment(request, gig, song=None)


@login_required
def add_song_comment(request, song_id):
    song = get_object_or_404(sbsong.models.Song, pk=song_id)
    return _add_comment(request, song.gig, song)


def _get_comments(request, gig, song):
    not_after = request.GET.get('not_after')
    not_before = request.GET.get('not_before')
    no_changes = request.GET.get('no_changes') is not None
    if song:
        qs = song.comments.all()
    else:
        qs = gig.comments.all()
    if not_before:
        qs = qs.filter(id__gt=not_before)
    if not_after:
        qs = qs.filter(id__lt=not_after)
    if no_changes:
        qs = qs.exclude(comment_type=sbgig.models.Comment.CT_SONG_EDIT)
        qs = qs.exclude(comment_type=sbgig.models.Comment.CT_GIG_EDIT)
    qs = qs.select_related('song', 'gig', 'author')
    comments = list(qs[:settings.SB_COMMENTS_ON_PAGE + 1])
    return render(request, 'sbgig/comments.html', {'comments': comments})


@login_required
def get_gig_comments(request, slug):
    gig = get_object_or_404(sbgig.models.Gig, slug=slug)
    return _get_comments(request, gig, song=None)


@login_required
def get_song_comments(request, song_id):
    song = get_object_or_404(sbsong.models.Song, pk=song_id)
    return _get_comments(request, song.gig, song)
