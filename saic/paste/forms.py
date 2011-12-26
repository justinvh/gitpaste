from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from models import *

class PasteForm(forms.Form):
    languages = (
            ("plain", "Plain Text"),
            ("bash", "Bash"),
            ("cpp", "C++"),
            ("css", "CSS"),
            ("html", "HTML"),
            ("java", "Java"),
            ("javascript", "JavaScript"),
            ("haskell", "Haskell"),
            ("lisp", "Lisp"),
            ("python", "Python"),
            ("scheme", "Scheme"),
            ("xml", "XML"),
            ("zsh", "Zsh")
    )
    description = forms.CharField(max_length=256, required=False,
            widget=forms.widgets.TextInput(attrs={
                'default': 'add a paste description...'
            }))

    filename = forms.CharField(max_length=256, required=False,
            widget=forms.widgets.TextInput(attrs={
                'default': 'add a file name...'
            }))

    paste = forms.CharField(widget=forms.Textarea, required=False)
    language = forms.ChoiceField(choices=languages, required=False)
