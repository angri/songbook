from django import forms

import sbuser.models
from sb.forms import BootstrapModelForm


class EditProfileForm(BootstrapModelForm):
    class Meta:
        model = sbuser.models.Profile
        fields = ['about_myself', 'gender']
        widgets = {
            'about_myself': forms.Textarea(attrs={'rows': 5})
        }
