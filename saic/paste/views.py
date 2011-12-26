from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.forms.formsets import formset_factory
from django.template.defaultfilters import slugify

from django.forms import ValidationError

from forms import PasteForm, SetForm
from models import Set, Paste, Commit

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import *

import git

import os
import settings
import string
import random

PasteSet = formset_factory(PasteForm)
PasteSetEdit = formset_factory(PasteForm, extra=0)

def paste(request):
    if request.method != 'POST':
        return render_to_response('paste.html', {
        'forms': PasteSet(),
        'set_form': SetForm()
        }, RequestContext(request))

    forms = PasteSet(request.POST)
    set_form = SetForm(request.POST)

    if not forms.is_valid() or not set_form.is_valid():
        return render_to_response('paste.html', {
        'forms': forms,
        'set_form': set_form,
        }, RequestContext(request))

    repodir = '%s/%s' % (
            settings.REPO_DIR,
            "".join(random.sample(string.letters + string.digits, 15)))
    os.mkdir(repodir)
    s = Set.objects.create(repo=repodir, 
            description=set_form.cleaned_data.get('description'))
    repo = git.Repo.init(repodir)
    index = repo.index
    commit = Commit.objects.create(set=s, commit='')

    for form_index, form in enumerate(forms):
        d = form.cleaned_data
        filename_original = d['filename']
        language, lang_lex = d['language'].split(';')
        paste=d['paste']

        filename = filename_original
        if not len(filename):
            filename = 'a-lonely-file'
            filename_original = 'a-lonely-file'

        filename_base, ext = os.path.splitext(filename)
        filename = slugify(filename[:len(ext)])
        absolute_path = '%s/%s%s' % (repodir, filename, ext)
        filename_base, ext = os.path.splitext(absolute_path)

        if not len(ext):
            absolute_path += language
            ext = language

        i = 1
        while os.path.exists(absolute_path):
            absolute_path = '%s-%d%s' % (filename_base, i, ext)
            i += 1

        f = open(absolute_path, "w")
        f.write(paste)
        f.close()

        lex = globals()[lang_lex]
        paste_formatted = highlight(paste, lex(), 
                HtmlFormatter(
                    linenos="table", 
                    lineanchors='line-%s' % form_index,
                    anchorlinenos=True))

        index.add([absolute_path])

        p = Paste.objects.create(
                filename=filename_original,
                absolute_path=absolute_path,
                paste=paste,
                paste_formatted=paste_formatted,
                language=d['language'],
                revision=commit)

        new_commit = index.commit('Initial paste.')
        commit.commit = new_commit
        commit.save()
    return redirect('paste_view', pk=s.pk)


def paste_view(request, pk):
    paste_set = get_object_or_404(Set, pk=pk)
    requested_commit = request.GET.get('commit')
    if requested_commit is None:
        commit = paste_set.commit_set.latest('id')
    else:
        commit = get_object_or_404(Commit, commit=requested_commit)
    pastes = commit.paste_set.all()
    return render_to_response('paste_view.html', {
        'paste_set': paste_set,
        'pastes': pastes,
        'commit_current': commit,
    }, RequestContext(request))


def paste_edit(request, pk):
    paste_set = get_object_or_404(Set, pk=pk)
    commit = paste_set.commit_set.latest('id')

    initial_data = []
    for paste in commit.paste_set.all():
        initial_data.append({
            'filename': paste.filename,
            'paste': paste.paste,
            'language': paste.language,
        })

    if request.method != 'POST':
        return render_to_response('paste.html', {
        'forms': PasteSetEdit(initial=initial_data),
        'set_form': SetForm(initial={ 'description': paste_set.description })
        }, RequestContext(request))

    forms = PasteSetEdit(request.POST, initial=initial_data)
    set_form = SetForm(request.POST, initial={ 'description': paste_set.description })

    if not forms.is_valid() or not set_form.is_valid():
        return render_to_response('paste.html', {
        'forms': forms,
        'set_form': set_form,
        }, RequestContext(request))

    repodir = paste_set.repo
    repo = git.Repo(repodir)
    index = repo.index
    s = paste_set
    commit = Commit.objects.create(set=s, commit='')

    for form_index, form in enumerate(forms):
        d = form.cleaned_data
        filename_original = d['filename']
        language, lang_lex = d['language'].split(';')
        paste=d['paste']

        filename = filename_original
        if not len(filename):
            filename = 'a-lonely-file'
            filename_original = 'a-lonely-file'

        filename_base, ext = os.path.splitext(filename)
        filename = slugify(filename[:len(ext)])
        absolute_path = '%s/%s%s' % (repodir, filename, ext)
        filename_base, ext = os.path.splitext(absolute_path)

        if not len(ext):
            absolute_path += language
            ext = language

        i = 1
        while os.path.exists(absolute_path):
            absolute_path = '%s-%d%s' % (filename_base, i, ext)
            i += 1

        f = open(absolute_path, "w")
        f.write(paste)
        f.close()

        lex = globals()[lang_lex]
        paste_formatted = highlight(paste, lex(), 
                HtmlFormatter(
                    linenos="table", 
                    lineanchors='line-%s' % form_index,
                    anchorlinenos=True))

        index.add([absolute_path])

        p = Paste.objects.create(
                filename=filename_original,
                absolute_path=absolute_path,
                paste=paste,
                paste_formatted=paste_formatted,
                language=d['language'],
                revision=commit)

        new_commit = index.commit('Modified.')
        commit.commit = new_commit
        commit.save()
    return redirect('paste_view', pk=s.pk)

def paste_delete(request, pk):
    pass


def paste_download(request, pk):
    pass

def find(request):
    pass
