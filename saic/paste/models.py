import pytz

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

import timezone

timezones = [(tz, tz) for tz in pytz.common_timezones]

class DateTimeFieldTZ(models.DateTimeField):
    def __init__(self, *args, **kwargs):
        super(DateTimeFieldTZ, self).__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        if self.auto_now or (self.auto_now_add and add):
            value = timezone.now()
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(DateTimeField, self).pre_save(model_instance, add)

    def get_prep_value(self, value):
        value = self.to_python(value)
        if value is not None and settings.USE_TZ and timezone.is_naive(value):
            default_timezone = timezone.get_default_timezone()
            value = timezone.make_aware(value, default_timezone)
        return value


class Set(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, default=None)
    description = models.CharField(max_length=255)
    repo = models.CharField(max_length=100)
    fork = models.ForeignKey('Commit', null=True, blank=True, default=None)
    created = DateTimeFieldTZ(auto_now=True)

    @property
    def email(self):
        return self.owner.preferences.email

    def __unicode__(self):
        return '%s: %s' % (self.repo, self.description)


class Commit(models.Model):
    commit = models.CharField(max_length=255)
    parent_set = models.ForeignKey(Set)
    created = DateTimeFieldTZ(auto_now=True)
    owner = models.ForeignKey(User, null=True, blank=True, default=None)
    diff = models.TextField()

    @property
    def email(self):
        return self.owner.preferences.email

    class Meta:
        ordering = ['-created']
        get_latest_by = 'created'

    def __unicode__(self):
        return '%s by %s' % (self.commit, self.owner)


class Comment(models.Model):
    parent = models.TextField(null=True, blank=True, default=None)
    diff = models.TextField(blank=True)
    commit = models.ForeignKey(Commit)
    owner = models.ForeignKey(User)
    comment = models.TextField()
    created = DateTimeFieldTZ(auto_now=True)

    @property
    def email(self):
        return self.owner.preferences.email

    def __unicode__(self):
        return '%s: %s' % (self.owner, self.commit.commit)


class Paste(models.Model):
    absolute_path = models.CharField(max_length=2048)
    filename = models.CharField(max_length=255)
    paste = models.TextField()
    paste_formatted = models.TextField()
    language = models.CharField(max_length=100)
    revision = models.ForeignKey(Commit)
    created = DateTimeFieldTZ(auto_now=True)
    priority = models.IntegerField()

    class Meta:
        ordering = ['priority']

    def __unicode__(self):
        return '%s: %s' % (self.filename, self.revision.commit)


class Favorite(models.Model):
    parent_set = models.ForeignKey(Set)
    user = models.ForeignKey(User)
    created = DateTimeFieldTZ(auto_now=True)

    def __unicode__(self):
        return '%s: %s' % (self.user, self.parent_set.repo)


class Preferences(models.Model):
    user = models.OneToOneField(User)
    mask_email = models.BooleanField()
    masked_email = models.EmailField()
    default_anonymous = models.BooleanField()
    timezone = models.CharField(blank=True, choices=timezones, max_length=20)
    gravatar = models.URLField(blank=True)

    @property
    def email(self):
        if self.mask_email:
            return self.masked_email
        return self.user.email

    def __unicode__(self):
        return "%s <%s>" % (self.user, self.masked_email)
