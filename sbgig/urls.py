from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^(?P<slug>[^/]+)$', views.view_gig, name='view-gig'),
    url(r'^(?P<slug>[^/]+)/edit$', views.edit_gig, name='edit-gig'),
    url(r'^(?P<slug>[^/]+)/add-comment$',
        views.add_gig_comment, name='add-gig-comment'),
    url(r'^add-song-comment/(?P<song_id>\d+)$',
        views.add_song_comment, name='add-song-comment'),

    url(r'^(?P<slug>[^/]+)/comments$',
        views.get_gig_comments, name='get-gig-comments'),
    url(r'^song-comments/(?P<song_id>\d+)$',
        views.get_song_comments, name='get-song-comments'),

    url(r'^(?P<slug>[^/]+)/setlist$',
        views.setlist, name='setlist'),
]
