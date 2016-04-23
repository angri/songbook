from django import forms

from sb.forms import BootstrapModelForm

import sbgig.models


class GigForm(BootstrapModelForm):
    class Meta:
        model = sbgig.models.Gig
        fields = ['title', 'slug', 'date', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'required': True}),
            'slug': forms.TextInput(attrs={'required': True}),
            'date': forms.TextInput(attrs={'type': 'date', 'required': True}),
            'description': forms.Textarea(attrs={'rows': 6})
        }
