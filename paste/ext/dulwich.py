# porcelain.py -- Class-based porcelain on top of Dulwich Repo
# Copyright (C) 2014 Joel Bennett <jaykul@huddledmasses.org>
#
# Some rights reserved.
#
# Redistribution and use in source and binary forms of the software as well as 
# documentation, with or without modification, are permitted provided that the 
# following conditions are met:
#
# - Redistributions of source code must retain the above copyright notice, 
# this list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright 
# notice, this list of conditions and the following disclaimer in the 
# documentation and/or other materials provided with the distribution.
#
# - The names of the contributors may not be used to endorse or promote 
# products derived from this software without specific prior written 
# permission.
#
# THIS SOFTWARE AND DOCUMENTATION IS PROVIDED BY THE COPYRIGHT HOLDERS AND 
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT 
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A 
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR 
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; 
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR 
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE AND 
# DOCUMENTATION, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Wrapper around Git for a local repository on top of dulwich.Repo
   Should be a plug-n-play replacement for paste.ext.git, just change models.py to:

   from paste.ext.dulwich import Git

Working:
 * init
 * add
 * rm
 * commit
 * files
 * log
 * show

Required:
 * archive
 * clone

"""

__docformat__ = 'restructuredText'

import os
import sys
import stat

from cStringIO import StringIO
from contextlib import closing

from dulwich import index
from dulwich.client import get_transport_and_path
from dulwich.patch import write_tree_diff
from dulwich.repo import (BaseRepo, Repo)
from dulwich.objects import (Tree, Commit)
from dulwich.server import update_server_info as server_update_server_info
from dulwich.errors import NotGitRepository

class Git:
    
    def __init__(self, repository):
        if isinstance(repository, BaseRepo):
            return repository
        if not(os.path.exists(repository)):
            self.repo = Repo.init(str(repository), mkdir=True)
        else:
            try:
                self.repo = Repo(str(repository))
            except NotGitRepository:
                self.repo = Repo.init(str(repository))
    
    def init(self):
        pass
    
    def add(self, paths=None):
        """Add files to the staging area of the Git repository.
        This does not commit the changes to the repository.
        
        :param paths: Paths to add
        """
        if isinstance(paths, basestring):
            paths = [str(paths)]
        
        # Make sure dulwich stores RELATIVE paths.
        paths = [str(os.path.relpath(path, self.repo.path)) for path in paths]
        
        self.repo.stage(paths)
    
    def rm(self, paths=None):
        """Remove files from the Git repository.
        This does not commit the changes to the repository.
        
        :param paths: Paths to remove
        """
        if isinstance(paths, basestring):
            paths = [str(paths)]
        
        # dulwich repository has RELATIVE paths, needs relative paths
        paths = [str(os.path.relpath(path, self.repo.path)) for path in paths]
        
        index = self.repo.open_index()
        for p in paths:
            del index[p]
        index.write()
    
    def _write_commit(self, outstream=sys.stdout, commit="HEAD"):
        """Write a readable commit log like git's
        
        :param outstream: A file-like stream to write to
        :param commit: A `Commit` object
        """
        
        if not(isinstance(commit, Commit)):
            commit = self.repo[str(commit)]
        
        outstream.write("-" * 50 + "\n")
        outstream.write("commit: %s\n" % commit.id)
        if len(commit.parents) > 1:
            outstream.write("merge: %s\n" % "...".join(commit.parents[1:]))
        outstream.write("author: %s\n" % commit.author)
        outstream.write("committer: %s\n" % commit.committer)
        outstream.write("\n")
        outstream.write(commit.message + "\n")
        outstream.write("\n")
    
    def commit(self, message=None, author=None, committer=None):
        """Create a new commit from all staged files.
        The specified message is used for the commit message,
        and the author and committer may be set as well.
        
        :param message: Optional commit message
        :param author: Optional author name and email
        :param committer: Optional committer name and email
        :return: SHA1 of the new commit
        """
        return self.repo.do_commit(message=message, author=author, committer=committer)
    
    def log(self):
        """Returns the commit log of the repository.
        """
        walker = self.repo.get_walker()
        
        with closing(StringIO()) as stream:
            for entry in walker:
                self._write_commit(stream, entry.commit)
            
            stream.seek(0)
            result = "".join(stream.readlines())
        
        return result
    
    def show(self, committish="HEAD"):
        """Print the changes in a commit (like diff, but for previous commits)
        
        :param committish: Commit to write
        """
        commit = self.repo[committish]
        parent_commit = self.repo[commit.parents[0]]
        with closing(StringIO()) as stream:
            self._write_commit(stream, commit)
            write_tree_diff(stream, self.repo.object_store, parent_commit.tree, commit.tree)
            stream.seek(0)
            result = "".join(stream.readlines())
        
        return result
    
    def files(self, committish="HEAD"):
        tree = self.repo[self.repo[committish].tree]
        for f in self._files(tree):
            yield f
    
    def _files(self, tree, path="."):
        for item in tree.items():
            name = os.path.join(path, item.path)
            print(name)
            if item.mode == stat.S_IFDIR:
                for child in self._files(self.repo[item.sha], name):
                    yield child
            else:
                yield name



    ## Pseudo code from dulwich.porcelain 
    ## This won't work here because of the 'client' stuff
    ## but it should help figure out what to do...

    #def archive(self, committish=None, outstream=sys.stdout, errstream=sys.stderr):
    #    """Create an archive.

    #    :param committish: Commit SHA1 or ref to use
    #    :param outstream: Output stream (defaults to stdout)
    #    :param errstream: Error stream (defaults to stderr)
    #    """
        
    #    client, path = get_transport_and_path(self.repo.path)
    #    if committish is None:
    #        committish = "HEAD"
    #    client.archive(path, committish, outstream.write, errstream.write)


    #def clone(self, path, bare=False, checkout=None, outstream=sys.stdout):
    #    """Clone a local or remote git repository.
        
    #    :param target: Path to target repository
    #    :param bare: Whether or not to create a bare repository
    #    :param outstream: Optional stream to write progress to
    #    :return: The new repository
    #    """
    #    if checkout is None:
    #        checkout = (not bare)
    #    if checkout and bare:
    #        raise ValueError("checkout and bare are incompatible")
    #    client, host_path = get_transport_and_path(self.repo.path)
        
    #    if not os.path.exists(target):
    #        os.mkdir(target)
    #    if bare:
    #        r = Repo.init_bare(target)
    #    else:
    #        r = Repo.init(target)
    #    remote_refs = client.fetch(host_path, r,
    #        determine_wants=r.object_store.determine_wants_all,
    #        progress=outstream.write)
    #    r["HEAD"] = remote_refs["HEAD"]
    #    if checkout:
    #        outstream.write('Checking out HEAD')
    #        index.build_index_from_tree(r.path, r.index_path(),
    #                                    r.object_store, r["HEAD"].tree)
        
    #    return r
