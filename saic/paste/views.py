import os
import settings
import string
import random

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import *

import git

from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.forms.formsets import formset_factory
from django.template.defaultfilters import slugify
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import auth
from django.forms import ValidationError

from forms import PasteForm, SetForm, UserCreationForm, CommentForm
from forms import CommitMetaForm
from models import Set, Paste, Commit, Favorite, Comment

PasteSet = formset_factory(PasteForm)
PasteSetEdit = formset_factory(PasteForm, extra=0)


def paste(request):
    if request.method != 'POST':
        return render_to_response('paste.html', {
            'forms': PasteSet(),
            'set_form': SetForm(),
            'commit_meta_form': CommitMetaForm()
        }, RequestContext(request))

    paste_forms = PasteSet(request.POST)
    set_form = SetForm(request.POST)
    commit_meta_form = CommitMetaForm(request.POST)

    if (not paste_forms.is_valid() or
            not set_form.is_valid() or
            not commit_meta_form.is_valid()):
        return render_to_response('paste.html', {
            'forms': paste_forms,
            'set_form': set_form,
            'commit_meta_form': commit_meta_form
        }, RequestContext(request))

    # Repositories are just a random sequence of letters and digits
    # We store the reference repository for editing the pastes.
    repo_dir = os.sep.join([
        settings.REPO_DIR,
        "".join(random.sample(string.letters + string.digits, 15))
    ])

    anonymous = commit_meta_form.cleaned_data['anonymous']

    os.mkdir(repo_dir)

    owner = None
    if request.user.is_authenticated() and not anonymous:
        owner = request.user

    # Create a new paste set so we can reference our paste.
    description = set_form.cleaned_data.get('description')
    paste_set = Set.objects.create(
            repo=repo_dir,
            owner=owner,
            description=description
    )

    # Yes, this is horrible. I know. But there is a bug with Python Git.
    # See: https://github.com/gitpython-developers/GitPython/issues/39
    os.environ['USER'] = "Anonymous"
    if owner:
        os.environ['USER'] = owner.username

    # Initialize a commit, git repository, and pull the current index.
    commit = Commit.objects.create(
            parent_set=paste_set,
            commit='',
            owner=owner
    )

    git_repo = git.Repo.init(repo_dir)
    index = git_repo.index

    # We enumerate over the forms so we can have a way to reference
    # the line numbers in a unique way relevant to the pastes.
    for form_index, form in enumerate(paste_forms):
        data = form.cleaned_data
        filename = data['filename']
        language, language_lex = data['language'].split(';')
        paste = data['paste']

        # If we don't specify a filename, then obviously it is lonely
        if not len(filename):
            filename = 'a-lonely-file'

        # Construct a more logical filename for our commit
        filename_base, ext = os.path.splitext(filename)
        filename_slugify = slugify(filename[:len(ext)])
        filename_absolute = os.sep.join([
            repo_dir,
            filename
        ])
        filename_absolute += ext
        filename_base, ext = os.path.splitext(filename_absolute)

        # If no extension was specified in the file, then we can append
        # the extension from the lexer.
        if not len(ext):
            filename_absolute += language
            ext = language

        # Gists doesn't allow for the same filename, we do.
        # Just append a number to the filename and call it good.
        i = 1
        while os.path.exists(filename_absolute):
            filename_absolute = '%s-%d%s' % (filename_base, i, ext)
            i += 1

        # Open the file, write the paste, call it good.
        f = open(filename_absolute, "w")
        f.write(paste)
        f.close()

        # This is a bit nasty and a get_by_ext something exist in pygments.
        # However, globals() is just much more fun.
        lex = globals()[language_lex]
        paste_formatted = highlight(
                paste,
                lex(),
                HtmlFormatter(
                    style='colorful',
                    linenos='table',
                    lineanchors='line-%s' % form_index,
                    anchorlinenos=True)
        )

        # Add the file to the index and create the paste
        index.add([filename_absolute])
        p = Paste.objects.create(
                filename=filename,
                absolute_path=filename_absolute,
                paste=paste,
                paste_formatted=paste_formatted,
                language=data['language'],
                revision=commit
        )

        # Create the commit from the index
        new_commit = index.commit('Initial paste.')
        commit.commit = new_commit
        commit.save()

    return redirect('paste_view', pk=paste_set.pk)


def paste_view(request, pk):
    paste_set = get_object_or_404(Set, pk=pk)
    requested_commit = request.GET.get('commit')

    # Meh, this could be done better and I am a bit disappointed that you
    # can't filter on the request.user if it is AnonymousUser, so we have
    # to do this request.user.is_authenticated()
    favorited = False
    if request.user.is_authenticated():
        favorited = Favorite.objects.filter(
                parent_set=paste_set,
                user=request.user).exists()

    # A requested commit allows us to navigate in history
    latest_commit = paste_set.commit_set.latest('created')
    if requested_commit is None:
        commit = latest_commit
    else:
        commit = get_object_or_404(Commit,
                parent_set=paste_set, commit=requested_commit)

    if request.method != 'POST':
        comment_form = CommentForm()
    else:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid() and request.user.is_authenticated():
            comment = Comment.objects.create(
                    commit=commit,
                    owner=request.user,
                    comment=comment_form.cleaned_data['comment']
            )

    return render_to_response('paste_view.html', {
        'paste_set': paste_set,
        'pastes': commit.paste_set.all().order_by('id'),
        'commit_current': commit,
        'favorited': favorited,
        'editable': latest_commit == commit,
        'comment_form': comment_form
    }, RequestContext(request))


def paste_edit(request, pk):
    paste_set = get_object_or_404(Set, pk=pk)
    requested_commit = request.GET.get('commit')

    # You can technically modify anything in history and update it
    if requested_commit is None:
        commit = paste_set.commit_set.latest('id')
    else:
        commit = get_object_or_404(Commit,
                parent_set=paste_set, commit=requested_commit)

    # Populate our initial data
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
            'commit_meta_form': CommitMetaForm()
        }, RequestContext(request))

    forms = PasteSetEdit(request.POST, initial=initial_data)
    commit_meta_form = CommitMetaForm(request.POST)

    if not forms.is_valid() or not commit_meta_form.is_valid():
        return render_to_response('paste.html', {
            'forms': forms,
        }, RequestContext(request))

    # Update the repo
    repo_dir = paste_set.repo
    repo = git.Repo(repo_dir)
    index = repo.index

    anonymous = commit_meta_form.cleaned_data['anonymous']

    owner = None
    if request.user.is_authenticated() and not anonymous:
        owner = request.user

    # Yes, this is horrible. I know. But there is a bug with Python Git.
    # See: https://github.com/gitpython-developers/GitPython/issues/39
    os.environ['USER'] = "Anonymous"
    if owner:
        os.environ['USER'] = owner.username

    commit = Commit.objects.create(
            parent_set=paste_set,
            commit='',
            owner=owner
    )

    # We enumerate over the forms so we can have a way to reference
    # the line numbers in a unique way relevant to the pastes.
    for form_index, form in enumerate(forms):
        data = form.cleaned_data
        filename = data['filename']
        language, language_lex = data['language'].split(';')
        paste = data['paste']

        # If we don't specify a filename, then obviously it is lonely
        if not len(filename):
            filename = 'a-lonely-file'

        # Construct a more logical filename for our commit
        filename_base, ext = os.path.splitext(filename)
        filename_slugify = slugify(filename[:len(ext)])
        filename_absolute = os.sep.join([
            repo_dir,
            filename
        ])
        filename_absolute += ext
        filename_base, ext = os.path.splitext(filename_absolute)

        # If no extension was specified in the file, then we can append
        # the extension from the lexer.
        if not len(ext):
            filename_absolute += language
            ext = language

        # Gists doesn't allow for the same filename, we do.
        # Just append a number to the filename and call it good.
        i = 1
        while os.path.exists(filename_absolute):
            filename_absolute = '%s-%d%s' % (filename_base, i, ext)
            i += 1

        # Open the file, write the paste, call it good.
        f = open(filename_absolute, "w")
        f.write(paste)
        f.close()

        # This is a bit nasty and a get_by_ext something exist in pygments.
        # However, globals() is just much more fun.
        lex = globals()[language_lex]
        paste_formatted = highlight(
                paste,
                lex(),
                HtmlFormatter(
                    style='colorful',
                    linenos='table',
                    lineanchors='line-%s' % form_index,
                    anchorlinenos=True)
        )

        # Add the file to the index and create the paste
        index.add([filename_absolute])
        p = Paste.objects.create(
                filename=filename,
                absolute_path=filename_absolute,
                paste=paste,
                paste_formatted=paste_formatted,
                language=data['language'],
                revision=commit
        )

        # Create the commit from the index
        new_commit = index.commit('Modified.')
        commit.commit = new_commit
        commit.save()

    return redirect('paste_view', pk=paste_set.pk)


@login_required
def paste_delete(request, pk):
    get_object_or_404(Set, pk=pk, owner=request.user).delete()
    return redirect('paste')


def paste_download(request, pk):
    pass


@login_required
def paste_favorite(request, pk):
    paste_set = get_object_or_404(Set, pk=pk)
    try:
        Favorite.objects.get(parent_set=paste_set, user=request.user).delete()
    except Favorite.DoesNotExist:
        Favorite.objects.create(parent_set=paste_set, user=request.user)
    return HttpResponse()


def paste_fork(request, pk):
    paste_set = get_object_or_404(Set, pk=pk)

    # Create the new repository
    repo_dir = os.sep.join([
        settings.REPO_DIR,
        "".join(random.sample(string.letters + string.digits, 15))
    ])
    os.mkdir(repo_dir)

    # Set the new owner
    owner = None
    if request.user.is_authenticated():
        owner = request.user

    # A requested commit allows us to navigate in history
    requested_commit = request.GET.get('commit')
    latest_commit = paste_set.commit_set.latest('created')
    if requested_commit is None:
        commit = latest_commit
    else:
        commit = get_object_or_404(Commit,
                parent_set=paste_set, commit=requested_commit)

    # Open the existing repository and navigate to a new head
    repo = git.Repo(paste_set.repo)
    clone = repo.clone(repo_dir)
    clone.git.reset(commit.commit)

    # Set the new owners
    old_commits = list(paste_set.commit_set.all().order_by('created'))
    paste_set.repo = repo_dir
    paste_set.fork = commit
    paste_set.pk = None
    paste_set.owner = owner
    paste_set.save()

    # Using list() forces evaluation, i.e. no lazy queries.
    # We want data.
    for old_commit in old_commits:
        pastes = list(old_commit.paste_set.all())
        old_commit.pk = None
        old_commit.parent_set = paste_set
        old_commit.owner = owner
        old_commit.save()
        for paste in pastes:
            paste.revision = old_commit
            paste.pk = None
            paste.save()
        if commit.commit == old_commit.commit:
            break

    return redirect('paste_view', pk=paste_set.pk)


@login_required
def paste_adopt(request, pk):
    paste_set = get_object_or_404(Set, pk=pk)
    if paste_set.owner is not None:
        return HttpResponse('This is not yours to own.')
    paste_set.owner = request.user
    paste_set.save()
    return redirect('paste_view', pk=paste_set.pk)


@login_required
def commit_adopt(request, pk):
    commit = get_object_or_404(Commit, pk=pk)
    if commit.owner is not None:
        return HttpResponse('This is not yours to own.')
    owner = request.user
    commit.owner = owner
    commit.save()
    return redirect('paste_view', pk=commit.parent_set.pk)


def find(request):
    pass


def register(request):
    """Handles the logic for registering a user into the system."""
    if request.method != 'POST':
        form = UserCreationForm()
        return render_to_response('register.html',
                {'form': form}, RequestContext(request))

    form = UserCreationForm(data=request.POST)

    if not form.is_valid():
        return render_to_response('register.html',
                {'form': form}, RequestContext(request))

    auth.logout(request)

    user = form.save(commit=False)
    user.email = user.username
    user.is_active = True
    user.save()

    authed_user = auth.authenticate(
            username=user.username,
            password=form.cleaned_data['password1']
    )

    auth.login(request, authed_user)
    return redirect('paste')


def login(request):
    """Handles the logic for logging a user into the system."""
    if request.method != 'POST':
        form = AuthenticationForm()
        return render_to_response('login.html',
                {'form': form}, RequestContext(request))

    form = AuthenticationForm(data=request.POST)
    if not form.is_valid():
        return render_to_response('login.html',
                {'form': form}, RequestContext(request))

    auth.login(request, form.get_user())
    return redirect(request.POST.get('next', 'paste'))


def logout(request):
    auth.logout(request)
    return redirect('login')


@login_required
def favorites(request):
    favorites = Favorite.objects.filter(user=request.user)
    return render_to_response('favorites.html',
            {'favorites': favorites}, RequestContext(request))


def user_pastes(request, owner=None):
    sets = Set.objects.filter(owner=owner)
    user = None
    if owner:
        user = User.objects.get(pk=owner)
    return render_to_response('user-pastes.html',
            {'sets': sets, 'owner': user}, RequestContext(request))


def users(request):
    users = User.objects.all()
    anons = Set.objects.filter(owner__isnull=True)
    return render_to_response('users.html',
            {'users': users, 'anons': anons}, RequestContext(request))
