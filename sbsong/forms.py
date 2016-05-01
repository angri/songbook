import uuid
import json
from itertools import chain

from django import forms
from django.forms.utils import flatatt
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from songbook.forms import BootstrapModelForm
import sbsong.models


class RangeSlider(forms.Select):
    def render(self, name, value, attrs=None, choices=()):
        did = "rs-%s" % (uuid.uuid4().hex, )
        choices = list(chain(self.choices, choices))
        if len(choices) < 2:
            raise ValueError('choices must have at least two items')
        minimum = choices[0][0]
        maximum = choices[-1][0]
        step = choices[1][0] - minimum
        for i in range(2, len(choices)):
            if choices[i][0] - choices[i - 1][0] != step:
                raise ValueError('step is not uniform across choices')
        if value is None:
            value = minimum
        attrs = attrs or {}
        attrs['min'] = minimum
        attrs['max'] = maximum
        attrs['step'] = step
        attrs['type'] = 'range'
        attrs['value'] = value
        final_attrs = self.build_attrs(attrs, name=name)
        output = ['<div class="rangeslider" id="%s">' % did]
        output.append(format_html('<input{}>', flatatt(final_attrs)))
        output.append('<span class="display-value"></span>')
        json_choices = json.dumps([
            (value, str(display)) for value, display in choices
        ])
        output.append('<script>$(function() { '
                      'sb.rangeSlider($("#%s"), %s); })'
                      '</script>' % (did, json_choices))
        output.append('</div>')
        return mark_safe('\n'.join(output))


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
        fields = ['notice', 'readiness']
        widgets = {
            'notice': forms.TextInput(
                attrs={'placeholder': _('Optional notice')}
            ),
            'readiness': RangeSlider(),
        }


class SongLinkForm(BootstrapModelForm):
    class Meta:
        model = sbsong.models.SongLink
        fields = ['link', 'notice']
        widgets = {
            'link': forms.TextInput(attrs={'required': 'true', 'type': 'url'})
        }
