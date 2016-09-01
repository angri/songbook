from django.db import models
from django.utils.translation import ugettext_lazy as _


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
