from django.db import models
from django.contrib.auth.models import User


class Set(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, default=None)
    repo = models.CharField(max_length=15)

class Paste(models.Model):
    description = models.CharField(max_length=255)
    filename = models.CharField(max_length=255)
    paste = models.TextField()
    paste_formatted = models.TextField()
    language = models.CharField(max_length=15)
    set = models.ForeignKey(Set)
