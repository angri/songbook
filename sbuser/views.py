from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages

import sb.models
import sbuser.forms


@login_required
def view_profile(request, username):
    user = get_object_or_404(User, username=username)
    user_plays = {up.instrument_id: up for up in user.plays.all()}
    all_instruments = [
        (instrument, user_plays.get(instrument.id))
        for instrument in sb.models.Instrument.objects.all()
    ]
    comments = user.song_comments.order_by('-datetime')[:5]
    is_editable = (user == request.user or request.user.is_superuser)
    return render(request, 'sbuser/view_profile.html',
                  {'user': user, 'all_instruments': all_instruments,
                   'comments': comments, 'is_editable': is_editable})


@login_required
def edit_profile(request, username):
    user = get_object_or_404(User, username=username)
    if not (user == request.user or request.user.is_superuser):
        return HttpResponse(status=403)
    user_plays = {up.instrument_id: up for up in user.plays.all()}
    all_instruments = [
        (instrument, user_plays.get(instrument.id))
        for instrument in sb.models.Instrument.objects.all()
    ]
    edit_form = sbuser.forms.EditProfileForm(request.POST or None,
                                             instance=user.profile)
    if edit_form.is_valid():
        edit_form.save()
        for instrument, user_plays in all_instruments:
            if request.POST.get('i_play_%d' % (instrument.id, )):
                notice = request.POST.get('i_play_%d_notice' %
                                          (instrument.id, ))
                if user_plays is None:
                    sb.models.UserPlays.objects.create(
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
    return render(request, 'sbuser/edit_profile.html',
                  {'user': user, 'all_instruments': all_instruments,
                   'edit_form': edit_form})


@login_required
def change_password(request):
    form = sbuser.forms.ChangePasswordForm(request.user, request.POST or None)
    if form.is_valid():
        form.save()
        messages.add_message(request, messages.INFO,
                             _('Password successfully changed'))
        return HttpResponseRedirect(reverse('sbuser:view-profile',
                                            args=[request.user.username]))
    return render(request, 'sbuser/change_password.html',
                  {'user': request.user, 'form': form})
