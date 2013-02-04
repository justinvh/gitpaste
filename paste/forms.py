from django import forms
from django.forms.formsets import formset_factory

from paste import ext


class PasteMetadataForm(forms.Form):
    description = forms.CharField(widget=forms.widgets.Textarea())


class PasteForm(forms.Form):
    filename = forms.CharField(max_length=255)
    paste = forms.CharField(widget=forms.widgets.Textarea())
    language = forms.ChoiceField(choices=ext.languages)


PasteFormSet = formset_factory(PasteForm)
