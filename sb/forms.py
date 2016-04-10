from django import forms
from django.forms.utils import ErrorList
from django.forms.forms import BoundField

import sb.models


def add_control_label(label_tag):
    def control_label_tag(self, contents=None, attrs=None, **kwargs):
        label_class = getattr(self.form, 'label_class', None)
        if label_class is not None:
            if attrs is None:
                attrs = {}
            attrs['class'] = label_class
        return label_tag(self, contents, attrs, **kwargs)
    return control_label_tag

BoundField.label_tag = add_control_label(BoundField.label_tag)


class CustomErrorList(ErrorList):
    def __init__(self, initlist=None, error_class='text-danger'):
        super(CustomErrorList, self).__init__(initlist, error_class)


class BootstrapModelForm(forms.ModelForm):
    error_css_class = 'has-error'
    label_class = 'control-label'

    def as_bootstrap_form(self):
        return self._html_output(
            normal_row='<div class="form-group"><div %(html_class_attr)s>'
                       '%(label)s%(field)s%(errors)s%(help_text)s</div></div>',
            error_row='<p class="help-block error-text">%s</p>',
            row_ender='</div></div>',
            help_text_html='<p class="help-block">%s</p>',
            errors_on_separate_row=False
        )

    def __init__(self, *args, **kwargs):
        super(BootstrapModelForm, self).__init__(*args, **kwargs)
        self.error_class = CustomErrorList
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


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
            'instrument', 'notice'
        ]
        widgets = {
            'instrument': forms.Select(attrs={'required': 'true'})
        }


class JoinSongPartForm(forms.ModelForm):
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
