from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^suggest-a-song', views.suggest_a_song),
    url(r'^song/(?P<song_id>\d+)/$', views.view_song),
    url(r'^join-part/(?P<part_id>\d+)$', views.join_song_part, name='join-song-part'),
]
