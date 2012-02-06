from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from models import *

from pygments import lexers

# Add preferred lexers here. This list will not be explicitly sorted. 
preferred_lexers = [
        'TextLexer', 
        'ActionScriptLexer', 
        'CLexer', 
        'CSharpLexer', 
        'CppLexer', 
        'CommonLispLexer', 
        'CssLexer',
        'DiffLexer',
        'ErlangLexer',
        'HaskellLexer',
        'HtmlLexer',
        'JavaLexer',
        'JavascriptLexer',
        'LuaLexer',
        'ObjectiveCLexer',
        'PerlLexer',
        'PhpLexer',
        'PythonLexer',
        'RubyLexer',
        'ScalaLexer',
        'SchemeLexer',
        'SqlLexer',
        'TexLexer',
        'XmlLexer',
]

def unwrap_lexer(lang):
    language = lexers.LEXERS[lang]
    lex, name, alias, exts, mime = language
    if len(exts):
        return ('%s;%s' % (lang, exts[0][1:]), name)
    return ('%s;.txt' % lang, name)


# Create our list of languages
base_languages = map(unwrap_lexer, lexers.LEXERS)
languages = map(unwrap_lexer, preferred_lexers)

# Only sort the base languages because we assume the preferred list is
# already in the desired sorting
base_languages.sort()

# Add the base cases and base languages
languages.append(('TextLexer;.txt', '----'),)
languages.extend(base_languages)

class CommitMetaForm(forms.Form):
    """These correspond to a particular commit or iteration of a paste."""
    anonymous = forms.BooleanField(required=False)

class SetMetaForm(forms.Form):
    """Extra set options"""
    anyone_can_edit = forms.BooleanField(required=False)
    private = forms.BooleanField(required=False)
    expires = forms.ChoiceField(
        choices = (
            ("never", "Never"),
            ("hour", "1 Hour"),
            ("day", "1 Day"),
            ("month", "1 Month"),
        ), required=False
    )

class SetForm(forms.Form):
    description = forms.CharField(max_length=256, required=False,
            widget=forms.widgets.TextInput(attrs={
                'placeholder': 'add a paste description...'
            }))

    def clean_description(self):
        d = self.cleaned_data.get('description')
        if d is None:
            return d
        if d == 'add a paste description...':
            return ''
        return d


class PasteForm(forms.Form):
    priority = forms.IntegerField(initial=0)
    filename = forms.CharField(max_length=256, required=False,
            widget=forms.widgets.TextInput(attrs={
                'placeholder': 'add a file name...',
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
    language = forms.ChoiceField(
            choices=languages,
            required=False,
            widget=forms.Select(attrs={'tabindex': -1})
    )


class UserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args,
**kwargs)

    class Meta:
        model = User
        exclude = ('date_joined', 'last_login', 'password')

    def save(self, commit=True):
        """See ProfileForm for this error."""
        model = super(UserCreationForm, self).save(commit=False)
        model.username = self.cleaned_data['username']

        if commit:
            model.save()

        return model


class CommentForm(forms.Form):
    comment = forms.CharField(required=True, widget=forms.Textarea)

class PreferenceForm(forms.ModelForm):
    class Meta:
        model = Preference
        exclude = ('user','masked_email','gravatar')
