from django import forms

from songbook.forms import BootstrapModelForm
import sb.models


class SongForm(BootstrapModelForm):
    class Meta:
        model = sb.models.Song
        fields = [
            'artist',
            'title',
            'description',
        ]


class SongPartForm(BootstrapModelForm):
    class Meta:
        model = sb.models.SongPart
        fields = [
            'instrument', 'notice', 'required',
        ]
        widgets = {
            'instrument': forms.Select(attrs={'required': 'true'})
        }


class JoinSongPartForm(BootstrapModelForm):
    class Meta:
        model = sb.models.SongPerformer
        fields = ['notice']
        widgets = {
            'notice': forms.TextInput(attrs={'placeholder': 'Optional notice'})
        }


class SongLinkForm(BootstrapModelForm):
    class Meta:
        model = sb.models.SongLink
        fields = ['link', 'notice']
        widgets = {
            'link': forms.TextInput(attrs={'required': 'true', 'type': 'url'})
        }
