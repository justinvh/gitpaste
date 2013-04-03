from django import forms
from django.forms.formsets import formset_factory

from paste import ext


class EmptyFormSetError(Exception):
    """A formset was expected, but there wasn't any"""


PasteEditorModeChoices = (('vim', 'Vim'),
                          ('emacs', 'Emacs'))

PasteTabChoices = ((2, '2'),
                   (4, '4'),
                   (8, '8'))

PasteTabTypeChoices = (('soft', 'Soft Tabs'),
                       ('hard', 'Hard Tabs'))


class PasteMetadataForm(forms.Form):
    description = forms.CharField(max_length=140, required=False)


class PasteForm(forms.Form):
    filename = forms.CharField(max_length=255, required=False)
    paste = forms.CharField(widget=forms.widgets.Textarea(), required=False)
    language = forms.ChoiceField(choices=ext.languages, required=False)
    tab_size = forms.ChoiceField(initial=1, choices=PasteTabChoices)
    tab_type = forms.ChoiceField(initial=1, choices=PasteTabTypeChoices)
    editor_mode = forms.ChoiceField(choices=PasteEditorModeChoices,
                                    initial='emacs')


PasteFormSet = formset_factory(PasteForm)
