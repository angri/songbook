import json
from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.contrib.syndication.views import Feed
from django.conf import settings
from django.utils.translation import ugettext_noop as _, ugettext
from django.utils import timezone

from songbook.jinja2env import format_datetime
import sbgig.models
import sbcomment.models


class GigCommentsFeed(Feed):
    description_template = "sbcomment/gig_feed_desc.html"
    EDIT_COMMENTS = set((
        sbcomment.models.Comment.CT_SONG_EDIT,
        sbcomment.models.Comment.CT_GIG_EDIT,
    ))

    def get_object(self, request, slug):
        return get_object_or_404(sbgig.models.Gig, slug=slug)

    def items(self, obj):
        max_datetime = (timezone.now()
                        - timedelta(seconds=settings.SB_UPDATE_COMMENT_GAP))
        comments = obj.comments.filter(datetime__lte=max_datetime)
        comments = comments[:settings.SB_COMMENTS_ON_PAGE]
        for comment in comments:
            comment.data = None
            comment.is_edit = False
            if comment.comment_type in self.EDIT_COMMENTS:
                comment.data = json.loads(comment.text)
                comment.is_edit = True
        return comments

    def title(self, obj):
        return ugettext("%(gig)s: comments and changes") % {'gig': obj.title}

    def link(self, obj):
        return obj.get_absolute_url()

    def description(self, obj):
        return self.title(obj)

    def item_title(self, item):
        if item.is_edit:
            action = item.data['action']
        elif item.comment_type == sbcomment.models.Comment.CT_SONG_COMMENT:
            action = (_('%(who)s (f) commented song %(when)s')
                      if item.author.profile.gender == 'f' else
                      _('%(who)s (m) commented song %(when)s'))
        elif item.comment_type == sbcomment.models.Comment.CT_GIG_COMMENT:
            action = (_('%(who)s (f) commented gig %(when)s')
                      if item.author.profile.gender == 'f' else
                      _('%(who)s (m) commented gig  %(when)s'))
        action = ugettext(action) % dict(who=item.author,
                                         when=format_datetime(item.datetime))
        if item.is_edit and 'changed_by' in item.data:
            action = ugettext("%(action)s / changes made by %(who)s") % \
                     dict(action=action, who=item.data['changed_by'])
        if item.song:
            return ugettext("%(song)s: %(action)s") % \
                            dict(song=item.song.title, action=action)
        else:
            return ugettext("%(gig)s: %(action)s") % \
                            dict(gig=item.gig.title, action=action)

    def item_author_name(self, item):
        return str(item.author)

    def item_pubdate(self, item):
        return item.datetime

    def item_link(self, item):
        if item.song:
            url = item.song.get_absolute_url()
        else:
            url = item.gig.get_absolute_url()
        return "%s#c%s" % (url, item.id)

    def item_guid(self, item):
        return str(item.id)
