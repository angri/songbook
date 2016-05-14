import sbgig.models


def all_gigs():
    return sbgig.models.Gig.objects.order_by('date')
