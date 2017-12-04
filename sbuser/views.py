from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib import messages

import sbsong.models
import sbuser.forms
import sbuser.models


def _get_user_performs(user, song_performer_qs):
    allgigs = []
    user_performs = song_performer_qs.filter(
        performer=user, part__song__gig__isnull=False
    ).select_related(
        'part', 'part__instrument', 'part__song', 'part__song__gig'
    ).order_by(
        '-part__song__gig', 'part__song', 'part'
    )
    for up in user_performs:
        if not allgigs or allgigs[-1][0].id != up.part.song.gig.id:
            allgigs.append((up.part.song.gig, []))
        gig, gigsongs = allgigs[-1]
        if not gigsongs or gigsongs[-1][0].id != up.part.song.id:
            gigsongs.append((up.part.song, []))
        song, songparts = gigsongs[-1]
        songparts.append((up.part, up))
    return allgigs


@login_required
def view_profile(request, username):
    user = get_object_or_404(User, username=username)
    user_plays = {up.instrument_id: up for up in user.plays.all()}
    all_instruments = [
        (instrument, user_plays.get(instrument.id))
        for instrument in sbsong.models.Instrument.objects.all()
    ]
    comments = user.comments.order_by('-datetime')[:5]
    is_editable = (user == request.user or request.user.is_superuser)

    upcoming_gigs = sbsong.models.SongPerformer.objects.filter(
        part__song__gig__date__gte=timezone.now().date()
    )
    past_gigs = sbsong.models.SongPerformer.objects.filter(
        part__song__gig__date__lt=timezone.now().date()
    )
    user_performs_past = _get_user_performs(user, past_gigs)
    user_performs_upcoming = _get_user_performs(user, upcoming_gigs)
    return render(request, 'sbuser/view_profile.html',
                  {'user': user, 'all_instruments': all_instruments,
                   'comments': comments, 'is_editable': is_editable,
                   'performs_past': user_performs_past,
                   'performs_upcoming': user_performs_upcoming})


@login_required
def edit_profile(request, username):
    user = get_object_or_404(User, username=username)
    if not (user == request.user or request.user.is_superuser):
        return HttpResponse(status=403)
    user_plays = {up.instrument_id: up for up in user.plays.all()}
    all_instruments = [
        (instrument, user_plays.get(instrument.id))
        for instrument in sbsong.models.Instrument.objects.all()
    ]
    edit_form = sbuser.forms.EditProfileForm(
        request.POST or None, instance=getattr(user, 'profile', None)
    )
    if edit_form.is_valid():
        profile = edit_form.save(commit=False)
        profile.user = user
        profile.save()
        for instrument, user_plays in all_instruments:
            if request.POST.get('i_play_%d' % (instrument.id, )):
                notice = request.POST.get('i_play_%d_notice' %
                                          (instrument.id, ))
                if user_plays is None:
                    sbuser.models.UserPlays.objects.create(
                        user=user, instrument=instrument, notice=notice
                    )
                elif user_plays.notice != notice:
                    user_plays.notice = notice
                    user_plays.save()
            elif user_plays is not None:
                user_plays.delete()
        messages.add_message(request, messages.INFO,
                             _('Profile successfully saved'))
        return HttpResponseRedirect(reverse('sbuser:view-profile',
                                            args=[username]))
    if not hasattr(user, 'profile'):
        messages.add_message(request, messages.WARNING,
                             _("Your profile is empty, please fill it below. "
                               "Than you can continue to songbook."))
    return render(request, 'sbuser/edit_profile.html',
                  {'user': user, 'all_instruments': all_instruments,
                   'edit_form': edit_form})


@login_required
def change_password(request):
    form = sbuser.forms.ChangePasswordForm(request.user, request.POST or None)
    if form.is_valid():
        form.save()
        request.user.profile.password_change_required = False
        request.user.profile.save()
        messages.add_message(request, messages.INFO,
                             _('Password successfully changed'))
        return HttpResponseRedirect(reverse('sbuser:view-profile',
                                            args=[request.user.username]))
    if request.user.profile.password_change_required:
        messages.add_message(request, messages.WARNING,
                             _("In order to continue you have to change your "
                               "password"))
    return render(request, 'sbuser/change_password.html',
                  {'user': request.user, 'form': form})
