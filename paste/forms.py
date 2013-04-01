from django import forms
from django.forms.formsets import formset_factory

from paste import ext


class PasteMetadataForm(forms.Form):
    description = forms.CharField(widget=forms.widgets.Textarea(), required=False)


class PasteForm(forms.Form):
    filename = forms.CharField(max_length=255, required=False)
    paste = forms.CharField(widget=forms.widgets.Textarea(), required=False)
    language = forms.ChoiceField(choices=ext.languages, required=False)


PasteFormSet = formset_factory(PasteForm)
