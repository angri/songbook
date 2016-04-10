from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^suggest-a-song', views.suggest_a_song),
    url(r'^song/(?P<song_id>\d+)/$', views.view_song),
    url(r'^join-part/(?P<part_id>\d+)$', views.join_song_part,
        name='join-song-part'),
    url(r'^leave-part/(?P<part_id>\d+)$', views.leave_song_part,
        name='leave-song-part'),
    url(r'^song/(?P<song_id>\d+)/add-a-part$', views.add_song_part,
        name='add-song-part'),
    url(r'^remove-part/(?P<part_id>\d+)$', views.remove_song_part,
        name='remove-song-part'),
    url(r'^song/(?P<song_id>\d+)/add-a-link$', views.add_song_link,
        name='add-song-link'),
    url(r'^remove-link/(?P<link_id>\d+)$', views.remove_song_link,
        name='remove-song-link'),
    url(r'^edit-link/(?P<link_id>\d+)$', views.edit_song_link,
        name='edit-song-link'),
]
