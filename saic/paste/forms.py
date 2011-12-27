from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from models import *

from pygments import lexers
languages = []
for i in lexers.LEXERS:
    language = lexers.LEXERS[i]
    lex, name, alias, exts, mime = language
    if len(exts):
        languages.append(('%s;%s' % (exts[0][1:], i), name))
languages.sort()
languages.insert(0, ('.txt;TextLexer', 'Plain Text'))

class SetForm(forms.Form):
    description = forms.CharField(max_length=256, required=False,
            widget=forms.widgets.TextInput(attrs={
                'default': 'add a paste description...'
            }))
    
    def clean_description(self):
        d = self.cleaned_data.get('description')
        if d is None:
            return d
        if d == 'add a paste description...':
            return ''
        return d


class PasteForm(forms.Form):
    filename = forms.CharField(max_length=256, required=False,
            widget=forms.widgets.TextInput(attrs={
                'default': 'add a file name...',
                'class': 'filename'
            }))

    def clean_filename(self):
        d = self.cleaned_data.get('filename')
        if d is None:
            return d
        if d == 'add a file name...':
            return ''
        return d


    paste = forms.CharField(widget=forms.Textarea, required=False)
    language = forms.ChoiceField(choices=languages, required=False,
            widget=forms.Select(attrs={
                'tabindex': -1
            }))
    make_anon = forms.BooleanField(required=False)


class UserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args,
**kwargs)

    class Meta:
        model = User
        exclude = ('username', 'date_joined', 'last_login', 'password')

    username = forms.EmailField() 

    def save(self, commit=True):
        """See ProfileForm for this error."""
        model = super(UserCreationForm, self).save(commit=False)
        model.username = self.cleaned_data['username']

        if commit:
            model.save()

        return model


class CommentForm(forms.Form):
    comment = forms.CharField(required=True, widget=forms.Textarea)
