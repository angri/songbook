from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^profile/(?P<username>.+)$',
        views.view_profile, name='view-profile'),
    url(r'^edit-profile/(?P<username>.+)$',
        views.edit_profile, name='edit-profile'),
    url(r'^change-password$', views.change_password, name='change-password'),
]
