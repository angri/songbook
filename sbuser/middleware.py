from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from . import views


class EmptyProfileMiddleware:
    def process_view(self, request, view_func, view_args, view_kwargs):
        if hasattr(request.user, 'profile'):
            return
        if view_func is views.edit_profile:
            return
        if not request.user.is_authenticated():
            return
        return HttpResponseRedirect(reverse('sbuser:edit-profile',
                                            args=[request.user.username]))
