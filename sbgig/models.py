import json

from django.db import models
from django.utils.translation import ugettext_noop, ugettext_lazy as _

import sbcomment.models


class Gig(models.Model):
    title = models.CharField(verbose_name=_("Gig name"),
                             max_length=60, blank=False)
    slug = models.SlugField(verbose_name=_("Slug"), blank=False)
    date = models.DateField(verbose_name=_("Gig date"), blank=False)
    description = models.TextField(verbose_name=_("Description"),
                                   null=False, blank=True)

    def __init__(self, *args, **kwargs):
        super(Gig, self).__init__(*args, **kwargs)
        self._pristine = {
            field.name: getattr(self, field.name)
            for field in self._meta.fields
        }

    def __str__(self):
        return "%s (%s)" % (self.title, self.date)

    def track_changes(self, user_making_changes):
        changes = []
        track_changes_of = [
            ('title', ugettext_noop('Gig name')),
            ('date', ugettext_noop('Gig date')),
            ('description', ugettext_noop('Description')),
        ]
        for field, verbose_name in track_changes_of:
            oldval = str(self._pristine[field] or '')
            newval = str(getattr(self, field))
            if oldval != newval:
                changes.append({
                    'title': verbose_name,
                    'title_translatable': True,
                    'prev': oldval,
                    'new': newval
                })
        if not changes:
            return
        action = (ugettext_noop('%(who)s (f) edited gig %(when)s')
                  if user_making_changes.profile.gender == 'f' else
                  ugettext_noop('%(who)s (m) edited gig %(when)s'))
        info = {'action': action, 'changes': changes}
        sbcomment.models.Comment.objects.create(
            gig=self, song=None, author=user_making_changes,
            text=json.dumps(info),
            comment_type=sbcomment.models.Comment.CT_GIG_EDIT,
        )
