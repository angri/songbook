from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db.models import Count

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
    return render(request, 'sbgig/view_gig.html',
                  {'gig': gig, 'unstaffed_songs': unstaffed_songs,
                   'staffed_songs': staffed_songs})


@login_required
def edit_gig(request, slug):
    gig = get_object_or_404(sbgig.models.Gig, slug=slug)
    form = sbgig.forms.GigForm(request.POST or None, instance=gig)
    if form.is_valid():
        form.save()
        messages.add_message(request, messages.INFO,
                             _("Gig successfully saved"))
        return HttpResponseRedirect(reverse('sbgig:view-gig', args=[slug]))
    return render(request, 'sbgig/edit_gig.html',
                  {'gig': gig, 'form': form})
