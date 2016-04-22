from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=1, choices=[
        ('f', _("Female")),
        ('m', _("Male")),
    ], default='m', verbose_name=_("Gender"))
    about_myself = models.TextField(verbose_name=_("About myself"),
                                    blank=True, null=False)
    password_change_required = models.BooleanField(default=True)

    def __str__(self):
        return "%s (%s)" % (self.user, self.gender)
