"""Wrapper around Git via sh."""
import os
from sh import git


class Git:
    def __init__(self, repository):
        git_dir = os.sep.join([repository, '.git'])
        work_tree = repository
        self.repository = repository
        self.pre_args = ('--git-dir={0}'.format(git_dir),
                         '--work-tree={0}'.format(work_tree))

    def add(self, filename):
        add_args = ('add', filename)
        full_args = self.pre_args + add_args
        return git(*full_args)

    def rm(self, filename):
        rm_args = ('rm', filename)
        full_args = self.pre_args + rm_args
        return git(*full_args)

    def commit(self, message, files='all'):
        commit_args = ('commit', '--message={0}'.format(message))
        if files == 'all':
            commit_args += ('-a',)
        else:
            commit_args += files
        full_args = self.pre_args + commit_args
        return git(*full_args)

    def init(self):
        return git.init(self.repository)

    def status(self):
        status_args = ('status',)
        full_args = self.pre_args + status_args
        return git(*full_args)

    def log(self):
        log_args = ('log', )
        full_args = self.pre_args + log_args
        return git(*full_args)

    def files(self):
        files_args = ('ls-tree', '--name-only', '-r', 'HEAD')
        full_args = self.pre_args + files_args
        return git(*full_args).splitlines()
