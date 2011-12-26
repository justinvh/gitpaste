from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.forms.formsets import formset_factory
from django.template.defaultfilters import slugify
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import auth

from django.forms import ValidationError

from forms import PasteForm, SetForm, UserCreationForm
from models import Set, Paste, Commit, Favorite

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

    if request.user.is_authenticated():
        owner = request.user

    s = Set.objects.create(repo=repodir, 
            owner=owner,
            description=set_form.cleaned_data.get('description'))
    repo = git.Repo.init(repodir)
    index = repo.index
    commit = Commit.objects.create(set=s, commit='', owner=owner)

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
                    style='colorful',
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
    favorited = Favorite.objects.filter(set=paste_set, user=request.user)
    if requested_commit is None:
        commit = paste_set.commit_set.latest('id')
    else:
        commit = get_object_or_404(Commit, commit=requested_commit)
    pastes = commit.paste_set.all()
    return render_to_response('paste_view.html', {
        'paste_set': paste_set,
        'pastes': pastes,
        'commit_current': commit,
        'favorited': len(favorited) > 0,
    }, RequestContext(request))


def paste_edit(request, pk):
    paste_set = get_object_or_404(Set, pk=pk)
    requested_commit = request.GET.get('commit')

    if requested_commit is None:
        commit = paste_set.commit_set.latest('id')
    else:
        commit = get_object_or_404(Commit, commit=requested_commit)

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

    owner = None
    if request.user.is_authenticated():
        owner = request.user

    commit = Commit.objects.create(set=s, commit='', owner=owner)

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
                    style='colorful',
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

@login_required
def paste_delete(request, pk):
    s = get_object_or_404(Set, pk=pk)
    if s.owner != request.user:
        return HttpResponse('This is not yours to delete.')
    s.delete()
    return redirect('paste')

def paste_download(request, pk):
    pass

@login_required
def paste_favorite(request, pk):
    s = get_object_or_404(Set, pk=pk)
    try:
        f = Favorite.objects.get(set=s, user=request.user)
        f.delete()
    except Favorite.DoesNotExist:
        Favorite.objects.create(set=s, user=request.user)
    return HttpResponse()

@login_required
def paste_adopt(request, pk):
    s = get_object_or_404(Set, pk=pk)
    if s.owner is not None:
        return HttpResponse('This is not yours to own.')
    s.owner = request.user
    s.save()
    return redirect('paste_view', pk=s.pk)

def commit_adopt(request, pk):
    commit = get_object_or_404(Commit, pk=pk)
    if commit.owner is not None:
        return HttpResponse('This is not yours to own.')
    owner = None
    if request.user.is_authenticated():
        owner = request.user
    commit.owner = owner
    commit.save()
    return redirect('paste_view', pk=commit.set.pk)
    

def find(request):
    pass

def register(request):
    """Handles the logic for registering a user into the system."""
    if request.method != 'POST':
        form = UserCreationForm()
        return render_to_response('register.html', 
                { 'form': form },
                RequestContext(request))

    form = UserCreationForm(data=request.POST)

    if not form.is_valid():
        return render_to_response('register.html', 
            { 'form': form },
            RequestContext(request))

    auth.logout(request)

    user = form.save(commit=False)
    user.email = user.username
    user.is_active = True
    user.save()

    authed_user = auth.authenticate(username=user.username, password=form.cleaned_data['password1'])
    auth.login(request, authed_user)

    return redirect('paste')

def login(request):
    """Handles the logic for logging a user into the system."""
    if request.method != 'POST':
        form = AuthenticationForm()
        return render_to_response('login.html', 
                { 'form': form }, RequestContext(request))

    form = AuthenticationForm(data=request.POST)
    if not form.is_valid():
        return render_to_response('login.html', 
            { 'form': form }, RequestContext(request))

    auth.login(request, form.get_user())
    
    next = request.POST.get('next')
    if next:
        return redirect(next)

    return redirect('paste')


def logout(request):
    auth.logout(request)
    return redirect('login')

