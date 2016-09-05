from django.conf.urls import url

from sbcomment import feeds


urlpatterns = [
    url(r'^feeds/(?P<slug>[^/]+)$', feeds.GigCommentsFeed(), name='view-gig'),
]
