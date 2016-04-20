from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User

import sb.models


def view_profile(request, username):
    user = get_object_or_404(User, username=username)
    user_plays = {up.instrument_id: up for up in user.plays.all()}
    all_instruments = [
        (instrument, user_plays.get(instrument.id))
        for instrument in sb.models.Instrument.objects.all()
    ]
    comments = user.song_comments.order_by('-datetime')[:5]
    return render(request, 'sbuser/view_profile.html',
                  {'user': user, 'all_instruments': all_instruments,
                   'comments': comments})
