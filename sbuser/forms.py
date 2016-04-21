from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.contrib.auth import authenticate

import sbuser.models
from sb.forms import BootstrapModelForm, BootstrapForm


class EditProfileForm(BootstrapModelForm):
    class Meta:
        model = sbuser.models.Profile
        fields = ['about_myself', 'gender']
        widgets = {
            'about_myself': forms.Textarea(attrs={'rows': 5})
        }


class ChangePasswordForm(BootstrapForm):
    old_password = forms.CharField(
        label=_("Old password"),
        widget=forms.PasswordInput(attrs={'required': True}),
        required=True, strip=False
    )
    new_password = forms.CharField(
        label=_("New password"), max_length=80,
        min_length=settings.MIN_PASSWORD_LENGTH,
        widget=forms.PasswordInput(attrs={'required': True}),
        required=True, strip=False
    )
    repeat_password = forms.CharField(
        label=_("Repeat password"), max_length=80,
        min_length=settings.MIN_PASSWORD_LENGTH,
        widget=forms.PasswordInput(attrs={'required': True}),
        required=True, strip=False
    )

    def __init__(self, user, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned_data = super(ChangePasswordForm, self).clean()
        opwd = cleaned_data.get('old_password')
        npwd1 = cleaned_data.get('new_password')
        npwd2 = cleaned_data.get('repeat_password')

        if opwd:
            if not authenticate(username=self.user.username, password=opwd):
                self.add_error('old_password', _("Password is incorrect"))
                return

        if npwd1 and npwd2:
            if npwd1 != npwd2:
                self.add_error('repeat_password', _("Passwords do not match."))
            else:
                try:
                    validate_password(npwd1, user=self.user)
                except forms.ValidationError as exc:
                    self.add_error('new_password', exc)
                if opwd == npwd1:
                    self.add_error('new_password', _("New password must differ"
                                                     " from an old one."))
        return cleaned_data

    def save(self):
        new_password = self.cleaned_data['new_password']
        self.user.set_password(new_password)
        self.user.save()
