"""Wrapper around Git via sh."""
import os
from sh import git


class Git:
    """Git is a class wrapper around sh.git. It provides an abstraction of
    certain git commands useful for quickly navigating a repository. The
    repository is navigated by defining the --work-tree and --git-dir of
    the external folder (which is the repo).

    """
    def __init__(self, repository):
        git_dir = os.sep.join([repository, '.git'])
        work_tree = repository
        self.repository = repository
        self.pre_args = ('--git-dir={0}'.format(git_dir),
                         '--work-tree={0}'.format(work_tree))

    def add(self, filename):
        """add -> STDOUT/STDERR of git add

        Adds a file given by filename to a Git repository. This does not
        commit the changes to the repository.

        """
        add_args = ('add', filename)
        full_args = self.pre_args + add_args
        return git(*full_args)

    def rm(self, filename):
        """rm -> STDOUT/STDERR of git rm

        Removes a file from the Git repository. This does not commit the
        changes to the repository.

        """
        rm_args = ('rm', filename)
        full_args = self.pre_args + rm_args
        return git(*full_args)

    def commit(self, message, files='all'):
        """commit -> STDOUT/STDERR of git commit

        Commits all files if files == 'all', otherwise commits files specified
        in the string of files. The given message is used inline for the
        commit mesage.

        """
        commit_args = ('commit', '--message="{0}"'.format(message))
        if files == 'all':
            commit_args += ('-a',)
        else:
            commit_args += files
        full_args = self.pre_args + commit_args
        return git(*full_args)

    def init(self):
        """init -> STDOUT/STDERR of git init

        Initializes a repository.

        """
        return git.init(self.repository)

    def status(self):
        """status -> STDOUT/STDERR of git status

        Reports the status of the repository.

        """
        status_args = ('status',)
        full_args = self.pre_args + status_args
        return git(*full_args)

    def log(self):
        """log -> STDOUT/STDERR of git log

        Reports the current log of the repository.

        """
        log_args = ('log', )
        full_args = self.pre_args + log_args
        return git(*full_args)

    def files(self):
        """files -> STDOUT/STDERR of git ls-tree

        Returns the files in the repository. Useful for iteration purposes.

        """
        files_args = ('ls-tree', '--name-only', '-r', 'HEAD')
        full_args = self.pre_args + files_args
        return git(*full_args).splitlines()
