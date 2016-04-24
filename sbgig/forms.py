from django import forms

from songbook.forms import BootstrapModelForm

import sbgig.models


class GigForm(BootstrapModelForm):
    class Meta:
        model = sbgig.models.Gig
        fields = ['title', 'date', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'required': True}),
            'date': forms.TextInput(attrs={'type': 'date', 'required': True}),
            'description': forms.Textarea(attrs={'rows': 6})
        }
