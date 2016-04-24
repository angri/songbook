from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

import sbgig.models


@login_required
def dashboard(request):
    latest_gig = sbgig.models.Gig.objects.order_by('-date')[0]
    return HttpResponseRedirect(reverse('sbgig:view-gig',
                                        args=[latest_gig.slug]))
