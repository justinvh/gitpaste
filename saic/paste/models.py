from django.db import models
from django.contrib.auth.models import User


class Set(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, default=None)
    description = models.CharField(max_length=255)
    repo = models.CharField(max_length=100)
    fork = models.ForeignKey('Commit', null=True, blank=True, default=None)
    created = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s: %s' % (self.repo, self.description)


class Commit(models.Model):
    commit = models.CharField(max_length=255)
    parent_set = models.ForeignKey(Set)
    created = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, null=True, blank=True, default=None)
    diff = models.TextField()

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        return '%s by %s' % (self.commit, self.owner)


class Comment(models.Model):
    parent = models.TextField(null=True, blank=True, default=None)
    diff = models.TextField(blank=True)
    commit = models.ForeignKey(Commit)
    owner = models.ForeignKey(User)
    comment = models.TextField()
    created = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s: %s' % (self.owner, self.commit.commit)


class Paste(models.Model):
    absolute_path = models.CharField(max_length=2048)
    filename = models.CharField(max_length=255)
    paste = models.TextField()
    paste_formatted = models.TextField()
    language = models.CharField(max_length=100)
    revision = models.ForeignKey(Commit)
    created = models.DateTimeField(auto_now=True)
    priority = models.IntegerField()

    class Meta:
        ordering = ['priority']

    def __unicode__(self):
        return '%s: %s' % (self.filename, self.revision.commit)


class Favorite(models.Model):
    parent_set = models.ForeignKey(Set)
    user = models.ForeignKey(User)
    created = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s: %s' % (self.user, self.parent_set.repo)
