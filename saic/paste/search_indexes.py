import datetime
from haystack.indexes import *
from haystack import site
from models import Paste, Commit

class CommitIndex(RealTimeSearchIndex):
    text = CharField(document=True, use_template=True)
    commit = CharField(model_attr='commit')
    created = DateField(model_attr='created')
    user = CharField(model_attr='owner', null=True)


class PasteIndex(RealTimeSearchIndex):
    text = CharField(document=True, use_template=True)
    paste = CharField(model_attr='paste')
    filename = CharField(model_attr='filename')
    language = CharField(model_attr='language')
    commit = CharField(model_attr='revision__commit')


site.register(Paste, PasteIndex)
site.register(Commit, CommitIndex)
