from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

class SettingsContextProcessor(object):
    """
    Class for creating simple context processors that
    return one or more Django settings.
    """

    def __init__(self, *setting_names):
        self.setting_names = setting_names

    def __call__(self, request):
        extra_context = {}
        for sn in self.setting_names:
            try:
                extra_context[sn] = getattr(settings, sn)
            except AttributeError, e:
                raise ImproperlyConfigured('Missing required setting: %s' % sn)
        return extra_context

use_tz = SettingsContextProcessor('USE_TZ')
use_icon = SettingsContextProcessor('USE_ICONS')

def tz(request):
    from django.utils import timezone
    return {'TIME_ZONE': timezone.get_current_timezone_name()}


def site(request):
    from django.contrib.sites.models import Site
    return {
        'site': Site.objects.get_current()
    }
