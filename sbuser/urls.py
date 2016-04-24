from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views
from . import forms


urlpatterns = [
    url(r'^(?P<username>.+)/profile$',
        views.view_profile, name='view-profile'),
    url(r'^(?P<username>.+)/edit-profile$',
        views.edit_profile, name='edit-profile'),
    url(r'^change-password$', views.change_password, name='change-password'),
    url(r'^login$', auth_views.login,
        {'authentication_form': forms.AuthenticationForm,
         'template_name': 'sbuser/login.html'},
        name='login'),
    url(r'^logout$', auth_views.logout,
        {'template_name': 'sbuser/logged_out.html'},
        name='logout'),
]
