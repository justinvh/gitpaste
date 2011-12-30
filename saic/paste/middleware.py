"""Timezone helper functions.

This module uses pytz when it's available and fallbacks when it isn't.
"""

from saic.paste.timezone import activate

class TimezoneMiddleware(object):
    def process_request(self, request):
        if request.user.is_authenticated():
            tz = request.user.preferences.timezone
            if tz:
                activate(tz)
