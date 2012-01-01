import datetime
from haystack.indexes import *
from haystack import site
from models import Paste, Commit


class CommitIndex(RealTimeSearchIndex):
    text = CharField(document=True, use_template=True)
    commit = CharField(model_attr='commit')
    user = CharField(model_attr='owner', null=True)

    def index_queryset(self):
        return Commit.objects.all()


class PasteIndex(RealTimeSearchIndex):
    text = CharField(document=True, use_template=True)
    paste = CharField(model_attr='paste')
    filename = CharField(model_attr='filename')
    language = CharField(model_attr='language')
    commit = CharField(model_attr='revision__commit')

    def index_queryset(self):
        return Paste.objects.all()


site.register(Paste, PasteIndex)
site.register(Commit, CommitIndex)
