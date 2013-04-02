import os
import logging
from paste.ext.git import Git

from collections import defaultdict

from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.conf import settings


logger = logging.getLogger(__name__)
_paste_memoize = defaultdict(lambda: None)


def clear_paste_memoization(pk):
    """clear_paste_memoization -> None
    Clears a model reference in the cache.

    """
    try:
        global _paste_memoize
        del _paste_memoize[pk]
    except KeyError:
        pass


def add_paste_memoization(pk, data):
    """add_paste_memoization -> object
    Adds data to the cache for a given pk.

    """
    global _paste_memoize
    _paste_memoize[pk] = data
    return data


def get_paste_memoization(pk):
    """get_paste_memoization -> object
    Returns associated content with an object.

    """
    return _paste_memoize[pk]


class Paste(models.Model):
    """A paste is a collection of files. It also acts as metadata for the
    files under the collection. A paste itself can be forked and marked as
    private.

    """
    owner = models.ForeignKey(
        User, null=True, blank=True,
        help_text=_("The owner of the paste. A null user implies an "
                    "anonymous user."))

    description = models.CharField(
        max_length=140, blank=True,
        help_text=_("A summary or quick detail of this paste."))

    repository = models.FilePathField(
        path=settings.GITPASTE_REPOSITORY, allow_files=False,
        allow_folders=True, help_text=_("The location of the Git repository"))

    private = models.BooleanField(
        default=False,
        help_text=_("If enabled, then this paste will only be accessible by "
                    "the original user or by a special URL."))

    private_key = models.CharField(
        max_length=5, blank=False,
        help_text=_("A small 5-character hash for private URL access"))

    views = models.IntegerField(default=0, help_text=_("The number of views"))
    created = models.DateTimeField(auto_now_add=True)
    fork = models.ForeignKey("Paste", null=True, blank=True)

    def __init__(self, *args, **kwargs):
        self._git = None
        super(Paste, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        """save -> Paste
        Saves the Paste object and creates the new repository.

        """
        import uuid
        self._git = None

        # Create the repository
        if self.pk is None:
            user = self.owner or "anonymous"
            folder = slugify(self.description)[:10] + '-' + str(uuid.uuid4())
            path = os.sep.join([settings.GITPASTE_REPOSITORY, user, folder])
            self.repository = path
            os.makedirs(path, mode=0o777, exist_ok=True)
            Git(self.repository).init()

        # Create the private key
        if self.pk is None:
            self.private_key = str(uuid.uuid4())[:5]

        return super(Paste, self).save(*args, **kwargs)

    def get_absolute_url(self):
        kwargs = {'pk': self.pk}
        if self.private:
            kwargs['key'] = self.private_key
        return reverse('paste.views.paste_view', kwargs=kwargs)

    def __unicode__(self):
        return self.repository

    def add_file(self, filename, content):
        """add_file -> None
        Adds a file to the repository.

        """
        if self.pk is None:
            raise Paste.DoesNotExist

        path = os.sep.join([self.repository, filename])

        commit_message = "Adds {0}".format(filename)
        if os.path.exists(path):
            commit_message = "Updates {0}".format(filename)

        with open(path, "w") as f:
            f.write(content)

        self.git.add(path)
        self.git.commit(commit_message)

    def delete_file(self, filename):
        """delete_files -> None
        Deletes a file from the repository.

        """
        if self.pk is None:
            raise Paste.DoesNotExist
        commit_message = "Removes {0}".format(filename)
        path = os.sep.join([self.repository, filename])
        self.git.rm(path)
        self.git.commit(commit_message)

    def status(self):
        """status -> string
        Retrieves the status of the repository.

        """
        if self.pk is None:
            raise Paste.DoesNotExist
        return self.git.status()

    def log(self):
        """status -> string
        Retrieves the status of the repository.

        """
        if self.pk is None:
            raise Paste.DoesNotExist
        return self.git.log()

    def files(self):
        """files -> [(filename, path, content), ...]
        Returns the files associated with the repository.

        """
        if self.pk is None:
            raise Paste.DoesNotExist

        memoized = get_paste_memoization(self.pk)
        if memoized is not None:
            return memoized

        data = []
        for filename in self.git.files():
            path = os.sep.join([self.repository, filename])
            content = open(path).read()
            size = len(content)
            data.append((filename, path, size, content))

        add_paste_memoization(self.pk, data)
        return data

    @property
    def git(self):
        if self.pk is None:
            raise Paste.DoesNotExist
        if self._git is None:
            self._git = Git(self.repository)
        return self._git


