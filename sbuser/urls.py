from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^profile/(?P<username>.+)$',
        views.view_profile, name='view-profile'),
]
