from django.utils import timezone

import sbgig.models


def all_gigs(*, only_future=False, only_past=False):
    gigs = sbgig.models.Gig.objects.order_by('date')
    if only_future:
        gigs = gigs.filter(date__gte=timezone.now().date())
    if only_past:
        gigs = gigs.filter(date__lt=timezone.now().date())
    return gigs
