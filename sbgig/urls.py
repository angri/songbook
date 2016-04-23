from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^(?P<slug>[^/]+)$', views.view_gig, name='view-gig'),
    url(r'^(?P<slug>[^/]+)/edit$', views.edit_gig, name='edit-gig'),
]
