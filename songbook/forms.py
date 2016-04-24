from django.forms.utils import ErrorList
from django.forms.forms import BoundField
from django import forms


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


class BootstrapFormMixin:
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

    def as_bootstrap_form_without_labels(self):
        return self._html_output(
            normal_row='<div class="form-group"><div %(html_class_attr)s>'
                       '%(field)s%(errors)s%(help_text)s</div></div>',
            error_row='<p class="help-block error-text">%s</p>',
            row_ender='</div></div>',
            help_text_html='<p class="help-block">%s</p>',
            errors_on_separate_row=False
        )

    def __init__(self, *args, **kwargs):
        super(BootstrapFormMixin, self).__init__(*args, **kwargs)
        self.error_class = CustomErrorList
        for field in self.fields:
            widget = self.fields[field].widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = 'checkbox'
            else:
                widget.attrs['class'] = 'form-control'


class BootstrapModelForm(BootstrapFormMixin, forms.ModelForm):
    pass


class BootstrapForm(BootstrapFormMixin, forms.Form):
    pass
