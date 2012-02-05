import os
import settings
import string
import random
import pytz
import tempfile
from datetime import datetime
from datetime import timedelta

from util import has_access_to_paste, user_owns_paste
from decorators import private
import timezone

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import *

import git

from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.utils.encoding import smart_str, smart_unicode
from django.forms.formsets import formset_factory
from django.template.defaultfilters import slugify
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import auth
from django.forms import ValidationError
from django.core.servers.basehttp import FileWrapper

from forms import PasteForm, SetForm, UserCreationForm, CommentForm
from forms import CommitMetaForm, SetMetaForm, PreferenceForm
from models import Set, Paste, Commit, Favorite, Comment, Preference

PasteSet = formset_factory(PasteForm)
PasteSetEdit = formset_factory(PasteForm, extra=0)


def send_zipfile(data, filename):
    temp = tempfile.TemporaryFile()
    temp.write(data)
    wrapper = FileWrapper(temp)
    response = HttpResponse(wrapper, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=' + filename +'.zip'
    response['Content-Length'] = temp.tell()
    temp.seek(0)
    return response


def _git_diff(git_commit_object, repo):
    diff = None
    try:
        transversed_commit = git_commit_object.traverse().next()
        has_history = True
        diff = repo.git.diff(
                transversed_commit.hexsha,
                git_commit_object.hexsha),

        if not len(diff):
            return None

        diff = highlight(
                repo.git.diff(
                    transversed_commit.hexsha,
                    git_commit_object.hexsha),
                DiffLexer(),
                HtmlFormatter(
                    style='colorful',
                    linenos='table',
                    lineanchors='diff',
                    anchorlinenos=True),
                )
        return diff
    except StopIteration, e:
        return None


def paste(request):
    commit_kwargs = {}
    if request.user.is_authenticated():
        commit_kwargs = {
                'anonymous': request.user.preference.default_anonymous
        }
    if request.method != 'POST':
        return render_to_response('paste.html', {
            'forms': PasteSet(),
            'set_form': SetForm(),
            'commit_meta_form': CommitMetaForm(initial=commit_kwargs),
            'set_meta_form': SetMetaForm(),
        }, RequestContext(request))

    paste_forms = PasteSet(request.POST)
    set_form = SetForm(request.POST)
    commit_meta_form = CommitMetaForm(request.POST, initial=commit_kwargs)
    set_meta_form = SetMetaForm(request.POST)

    if (not paste_forms.is_valid() or
            not set_form.is_valid() or
            not commit_meta_form.is_valid() or
            not set_meta_form.is_valid()):
        return render_to_response('paste.html', {
            'forms': paste_forms,
            'set_form': set_form,
            'commit_meta_form': commit_meta_form,
            'set_meta_form': set_meta_form,
        }, RequestContext(request))

    # Repositories are just a random sequence of letters and digits
    # We store the reference repository for editing the pastes.
    repo_dir = os.sep.join([
        settings.REPO_DIR,
        "".join(random.sample(string.letters + string.digits, 15))
    ])

    anonymous = commit_meta_form.cleaned_data.get('anonymous')

    os.mkdir(repo_dir)

    owner = None
    if request.user.is_authenticated() and not anonymous:
        owner = request.user

    description = set_form.cleaned_data.get('description')
    private = set_meta_form.cleaned_data.get('private')
    allow_edits = set_meta_form.cleaned_data.get('anyone_can_edit')

    # Calculate expiration time of set if necessary
    exp_option = set_meta_form.cleaned_data.get('expires')
    exp_map = {
        'day'   : timedelta(days=1),
        'hour'  : timedelta(hours=1),
        'month' : timedelta(365/12),
    }
    exp_time = datetime.utcnow() + exp_map[exp_option] if exp_option in exp_map else None

    # Generate a random hash for private access (20-30 characters from letters & numbers)
    private_key = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(random.randrange(20,30)))

    # Create a new paste set so we can reference our paste.
    paste_set = Set.objects.create(
            views=0,
            repo=repo_dir,
            owner=owner,
            description=description,
            private=private,
            anyone_can_edit=allow_edits,
            private_key=private_key,
            expires=exp_time,
    )

    # Yes, this is horrible. I know. But there is a bug with Python Git.
    # See: https://github.com/gitpython-developers/GitPython/issues/39
    os.environ['USER'] = "Anonymous"
    if owner:
        os.environ['USER'] = owner.username

    # Initialize a commit, git repository, and pull the current index.
    commit = Commit.objects.create(
            views=0,
            parent_set=paste_set,
            commit='',
            owner=owner
    )

    git_repo = git.Repo.init(repo_dir)
    index = git_repo.index

    # We enumerate over the forms so we can have a way to reference
    # the line numbers in a unique way relevant to the pastes.
    priority_filename = os.sep.join([repo_dir, 'priority.txt'])
    priority_file = open(priority_filename, 'w')
    for form_index, form in enumerate(paste_forms):
        data = form.cleaned_data
        filename = data['filename']
        language_lex, language = data['language'].split(';')
        paste = data['paste']

        # If we don't specify a filename, then obviously it is lonely
        if not len(filename):
            filename = 'paste'

        # Construct a more logical filename for our commit
        filename_base, ext = os.path.splitext(filename)
        filename_slugify = slugify(filename[:len(ext)])
        filename_absolute = os.sep.join([
            repo_dir,
            filename
        ])
        filename_absolute += ext
        filename_abs_base, ext = os.path.splitext(filename_absolute)

        # If no extension was specified in the file, then we can append
        # the extension from the lexer.
        if not len(ext):
            filename_absolute += language
            filename += language
            ext = language

        # Gists doesn't allow for the same filename, we do.
        # Just append a number to the filename and call it good.
        i = 1
        while os.path.exists(filename_absolute):
            filename_absolute = '%s-%d%s' % (filename_abs_base, i, ext)
            filename = '%s-%d%s' % (filename_base, i, ext)
            i += 1

        cleaned = []
        paste = paste.encode('UTF-8')
        for line in paste.split('\n'):
            line = line.rstrip()
            cleaned.append(line)
        paste = '\n'.join(cleaned)

        # Open the file, write the paste, call it good.
        f = open(filename_absolute, "w")
        f.write(paste)
        f.close()
        priority_file.write('%s: %s\n' % (filename, data['priority']))
        paste = smart_unicode(paste)

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
                priority=data['priority'],
                paste_formatted=paste_formatted,
                language=data['language'],
                revision=commit
        )

    # Add a priority file
    priority_file.close()
    index.add([priority_filename])

    # Create the commit from the index
    new_commit = index.commit('Initial paste.')
    commit.diff = 'No history.'
    commit.commit = new_commit

    commit.save()

    if not paste_set.private:
        return redirect('paste_view', pk=paste_set.pk)
    else:
        return redirect('paste_view', pk=paste_set.pk, private_key=paste_set.private_key)


@private(Set)
def paste_view(request, pk, paste_set, private_key=None):
    requested_commit = request.GET.get('commit')

    # Increment the views
    if not paste_set.views:
        paste_set.views = 0
    paste_set.views += 1
    paste_set.save()
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

    if not commit.views:
        commit.views = 0
    commit.views += 1
    commit.save()

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid() and request.user.is_authenticated():
            comment = Comment.objects.create(
                    commit=commit,
                    owner=request.user,
                    comment=comment_form.cleaned_data['comment']
            )

    editable = False
    if paste_set.anyone_can_edit or paste_set.owner == request.user:
        if latest_commit == commit:
            editable = True

    # Always clear the comment form
    comment_form = CommentForm()
    return render_to_response('paste_view.html', {
        'paste_set': paste_set,
        'pastes': commit.paste_set.all(),
        'commit_current': commit,
        'favorited': favorited,
        'editable': editable, 
        'comment_form': comment_form,
    }, RequestContext(request))


@private(Set)
def paste_edit(request, pk, paste_set, private_key=None):
    requested_commit = request.GET.get('commit')

    # You can technically modify anything in history and update it
    if requested_commit is None:
        commit = paste_set.commit_set.latest('id')
    else:
        commit = get_object_or_404(Commit,
                parent_set=paste_set, commit=requested_commit)

    previous_files = []
    for f in commit.paste_set.all():
        previous_files.append(os.path.basename(f.absolute_path))

    # Populate our initial data
    initial_data = []
    for paste in commit.paste_set.all():
        initial_data.append({
            'filename': paste.filename,
            'paste': paste.paste,
            'language': paste.language,
        })
    initial_set_meta = {
        'private': paste_set.private,
        'expires': paste_set.expires or "never",
        'anyone_can_edit': paste_set.anyone_can_edit 
    }

    #TODO: turn this into a template tag and allow template to do conversion
    original_expires_time = paste_set.expires
    expires_time = None
    if original_expires_time:
        if timezone.is_naive(original_expires_time):
            original_expires_time = original_expires_time.replace(tzinfo=timezone.utc)
        expires_time = original_expires_time.astimezone(timezone.get_current_timezone())

    if request.method != 'POST':
        set_form = None
        if request.user == paste_set.owner:
            set_form_initial = {'description': paste_set.description}
            set_form = SetForm(initial=set_form_initial)
        return render_to_response('paste.html', {
            'forms': PasteSetEdit(initial=initial_data),
            'set_form': set_form,
            'commit_meta_form': CommitMetaForm(),
            'set_meta_form': SetMetaForm(initial=initial_set_meta),
            'expires_time': expires_time,
            'editing': True,
        }, RequestContext(request))

    set_form = None
    set_meta_form = None
    forms = PasteSetEdit(request.POST, initial=initial_data)
    commit_meta_form = CommitMetaForm(request.POST)
    form_list = [forms, commit_meta_form]
    if request.user == paste_set.owner:
        set_form = SetForm(request.POST)
        set_meta_form = SetMetaForm(request.POST)
        form_list += [set_form, set_meta_form]

    if not all(map(lambda x: x.is_valid(), form_list)):
        return render_to_response('paste.html', {
            'forms': forms,
            'set_form': set_form,
            'commit_meta_form': commit_meta_form,
            'set_meta_form': set_meta_form,
            'expires_time': expires_time,
            'editing': True,
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

    if set_form:
        fdata = set_form.cleaned_data
        paste_set.description = fdata['description']

    if set_meta_form:
        fdata = set_meta_form.cleaned_data
        paste_set.private = fdata.get('private')
        paste_set.anyone_can_edit = fdata.get('anyone_can_edit')

    paste_set.save()

    commit = Commit.objects.create(
            views=0,
            parent_set=paste_set,
            commit='',
            owner=owner
    )

    # We enumerate over the forms so we can have a way to reference
    # the line numbers in a unique way relevant to the pastes.
    form_files = []
    priority_filename = os.sep.join([repo_dir, 'priority.txt'])
    priority_file = open(priority_filename, 'w')
    for form_index, form in enumerate(forms):
        data = form.cleaned_data
        filename = data['filename']
        language_lex, language = data['language'].split(';')
        paste = data['paste']

        # If we don't specify a filename, then obviously it is lonely
        no_filename = False
        if not len(filename):
            no_filename = True
            filename = 'paste' 

        # Construct a more logical filename for our commit
        filename_base, ext = os.path.splitext(filename)
        filename_slugify = slugify(filename[:len(ext)])
        filename_absolute = os.sep.join([
            repo_dir,
            filename
        ])
        filename_absolute += ext
        filename_abs_base, ext = os.path.splitext(filename_absolute)

        # If no extension was specified in the file, then we can append
        # the extension from the lexer.
        if not len(ext):
            filename_absolute += language
            filename += language
            ext = language

        # Gists doesn't allow for the same filename, we do.
        # Just append a number to the filename and call it good.
        i = 1
        if no_filename:
            while os.path.exists(filename_absolute):
                filename_absolute = '%s-%d%s' % (filename_abs_base, i, ext)
                filename = '%s-%d%s'(filename_base, i, ext)
                i += 1

        form_files.append(os.path.basename(filename_absolute))

        cleaned = []
        paste = paste.encode('UTF-8')
        for line in paste.split('\n'):
            line = line.rstrip()
            cleaned.append(line)
        paste = '\n'.join(cleaned)

        # Open the file, write the paste, call it good.
        f = open(filename_absolute, "w")
        f.write(paste)
        f.close()
        priority_file.write('%s: %s\n' % (filename, data['priority']))

        # This is a bit nasty and a get_by_ext something exist in pygments.
        # However, globals() is just much more fun.
        paste = smart_unicode(paste)
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
                priority=data['priority'],
                paste_formatted=paste_formatted,
                language=data['language'],
                revision=commit
        )

    # Create the commit from the index
    intersected = set(form_files).intersection(previous_files)
    removed_files = list(set(previous_files) - intersected)
    for f in removed_files:
        index.remove([os.sep.join([
            repo_dir,
            f
        ])])
    priority_file.close() 
    index.add([priority_filename])
    new_commit = index.commit('Modified.')
    commit.commit = new_commit
    commit.diff = _git_diff(new_commit, repo)
    if not commit.diff:
        commit.diff = 'Blank file or paste attributes changed.'
    commit.save()

    if not paste_set.private:
        return redirect('paste_view', pk=paste_set.pk)
    else:
        return redirect('paste_view', pk=paste_set.pk, private_key=paste_set.private_key)


@login_required
@private(Set)
def paste_delete(request, pk, paste_set, private_key=None):
    paste_set.delete()
    return redirect('paste')


@login_required
@private(Set)
def paste_favorite(request, pk, paste_set, private_key=None):
    try:
        Favorite.objects.get(parent_set=paste_set, user=request.user).delete()
    except Favorite.DoesNotExist:
        Favorite.objects.create(parent_set=paste_set, user=request.user)
    return HttpResponse()


@private(Set)
def paste_fork(request, pk, paste_set, private_key=None):
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

@private(Paste)
def paste_raw(request, pk, paste, private_key=None):
    filename = paste.filename
    response = HttpResponse(paste.paste, mimetype='application/force-download')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response


@login_required
@private(Set)
def paste_adopt(request, pk, paste_set, private_key=None):
    if paste_set.owner is not None:
        return HttpResponse('This is not yours to own.')
    paste_set.owner = request.user
    paste_set.save()
    return redirect('paste_view', pk=paste_set.pk)


@login_required
@private(Commit)
def commit_adopt(request, pk, commit, private_key=None):
    if commit.owner is not None:
        return HttpResponse('This is not yours to own.')
    owner = request.user
    commit.owner = owner
    commit.save()
    return redirect('paste_view', pk=commit.parent_set.pk)


@login_required
@private(Commit)
def commit_download(request, pk, commit, private_key=None):
    sha1 = commit.commit
    git_repo = git.Repo.init(commit.parent_set.repo)
    description = commit.parent_set.description
    filename = 'paste %s %s %s' % (commit.email, description, commit.short)
    filename = slugify(filename)
    return send_zipfile(git_repo.git.archive(sha1, format='zip'), filename) 


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
    if owner == None or request.user.id == None or request.user.pk != user.pk:
        sets = sets.exclude(private=True)
    return render_to_response('user-pastes.html',
            {'sets': sets, 'owner': user}, RequestContext(request))


def users(request):
    users = User.objects.all()
    anons = Set.objects.filter(owner__isnull=True).exclude(private=True)

    # This is an inefficient way to get the public sets for each user, should
    # be changed at some point to scale better with large # of users
    for user in users:
        if request.user.id == None or user.pk != request.user.pk:
            user.public_sets = user.set_set.exclude(private=True)
        else:
            user.public_sets = user.set_set

    return render_to_response('users.html',
            {'users': users, 'anons': anons}, RequestContext(request))


@login_required
def preference(request):
    saved = False
    instance = Preference.objects.get(user=request.user)
    preference = PreferenceForm(instance=instance)
    if request.method == 'POST':
        preference = PreferenceForm(data=request.POST, instance=instance)
        if preference.is_valid():
            p = preference.save(commit=False)
            p.save()
            saved = True
    return render_to_response('preference.html',
            { 'form': preference, 'saved': saved }, RequestContext(request))


def set_timezone(request):
    if request.method == 'POST':
        request.session[session_key] = pytz.timezone(request.POST['timezone'])
        return redirect('/')
    else:
        return render(request, 'template.html', {'timezones': pytz.common_timezones})

