import pytz

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

import timezone

from datetime import datetime

from saic.settings import generate_icon

timezones = [(tz, tz) for tz in pytz.common_timezones]

class DateTimeFieldTZ(models.DateTimeField):
    def __init__(self, *args, **kwargs):
        super(DateTimeFieldTZ, self).__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        if self.auto_now or (self.auto_now_add and add):
            value = datetime.utcnow().replace(tzinfo=timezone.utc)
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(models.DateTimeField, self).pre_save(model_instance, add)

    def get_prep_value(self, value):
        value = self.to_python(value)
        if value is not None and settings.USE_TZ and timezone.is_naive(value):
            # Always store times in UTC regardless of TIME_ZONE setting
            default_timezone = timezone.utc
            value = timezone.make_aware(value, default_timezone)
        return value


class Set(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, default=None)
    description = models.CharField(max_length=255)
    repo = models.CharField(max_length=100)
    fork = models.ForeignKey('Commit', null=True, blank=True, default=None, on_delete=models.SET_NULL)
    private = models.BooleanField(default=False)
    anyone_can_edit = models.BooleanField(default=False)
    private_key = models.CharField(max_length=30)
    expires = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    views = models.IntegerField()

    class Meta:
        ordering = ['-created']
        get_latest_by = 'created'

    @property
    def email(self):
        return self.owner.preference.email

    @property
    def active_private_key(self):
        """ For use in templates. """
        return self.private_key if self.private else ''

    @property
    def ordered_commits(self):
        return self.commit_set.order_by('-created', ).all

    def __unicode__(self):
        return '%s: %s' % (self.repo, self.description)


class Commit(models.Model):
    commit = models.CharField(max_length=255)
    parent_set = models.ForeignKey(Set)
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, null=True, blank=True, default=None)
    diff = models.TextField(null=True, blank=True)
    views = models.IntegerField()

    @property
    def email(self):
        return self.owner.preference.email if self.owner else "Anonymous"

    @property
    def short(self):
        return self.commit[:8]

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
    created = models.DateTimeField(auto_now_add=True)

    @property
    def email(self):
        return self.owner.preference.email

    def __unicode__(self):
        return '%s: %s' % (self.owner, self.commit.commit)


class Paste(models.Model):
    absolute_path = models.CharField(max_length=2048)
    filename = models.CharField(max_length=255)
    paste = models.TextField()
    paste_formatted = models.TextField()
    language = models.CharField(max_length=100)
    revision = models.ForeignKey(Commit)
    created = models.DateTimeField(auto_now_add=True)
    priority = models.IntegerField()

    class Meta:
        ordering = ['priority']

    def __unicode__(self):
        return '%s: %s' % (self.filename, self.revision.commit)


class Favorite(models.Model):
    parent_set = models.ForeignKey(Set)
    user = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s: %s' % (self.user, self.parent_set.repo)


class Preference(models.Model):
    user = models.OneToOneField(User, unique=True)
    mask_email = models.BooleanField(default=False)
    masked_email = models.CharField(max_length=256)
    default_anonymous = models.BooleanField()
    timezone = models.CharField(blank=True, choices=timezones, default='UTC', max_length=20)
    gravatar = models.URLField(blank=True)

    @property
    def email(self):
        if self.mask_email:
            return self.masked_email
        return self.user.email

    def __unicode__(self):
        return "%s <%s>" % (self.user, self.masked_email)


def get_or_create_preference(user):
    try:
        preference = Preference.objects.get(user=user)
    except Preference.DoesNotExist:
        try:
            at, email = str(user.email).split('@')
            masked_email = '%s%s@%s' % (at[:2], len(at[2:]) * '*', email)
        except ValueError, e:
            email = user.username
            masked_email = ''
        return Preference.objects.create(
                user=user, masked_email=masked_email, 
                gravatar=generate_icon(user.email)
        )
    return preference

User.preference = property(lambda u: get_or_create_preference(u))
