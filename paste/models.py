from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


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
        max_length=120, blank=True,
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

    views = models.IntegerField(help_text=_("The number of views"))
    created = models.DateTimeField(auto_Now_add=True)
    fork = models.ForeignKey("Paste", null=True, blank=True)
