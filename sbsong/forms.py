from django import forms
from django.utils.translation import ugettext_lazy as _

from songbook.forms import BootstrapModelForm
import sbsong.models


class SongForm(BootstrapModelForm):
    class Meta:
        model = sbsong.models.Song
        fields = [
            'title',
            'artist',
            'description',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'required': 'true'}),
            'artist': forms.TextInput(attrs={'required': 'true'}),
        }


class SongPartForm(BootstrapModelForm):
    class Meta:
        model = sbsong.models.SongPart
        fields = [
            'instrument', 'notice', 'required',
        ]
        widgets = {
            'instrument': forms.Select(attrs={'required': 'true'})
        }


class JoinSongPartForm(BootstrapModelForm):
    class Meta:
        model = sbsong.models.SongPerformer
        fields = ['notice']
        widgets = {
            'notice': forms.TextInput(
                attrs={'placeholder': _('Optional notice')}
            )
        }


class SongLinkForm(BootstrapModelForm):
    class Meta:
        model = sbsong.models.SongLink
        fields = ['link', 'notice']
        widgets = {
            'link': forms.TextInput(attrs={'required': 'true', 'type': 'url'})
        }
