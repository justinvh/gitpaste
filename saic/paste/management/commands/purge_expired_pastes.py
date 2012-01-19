from django.core.management.base import BaseCommand, CommandError
from saic.paste.models import Set
from datetime import datetime

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        expired_sets = Set.objects.filter(expires__lte=datetime.now())
        num_purged = expired_sets.count()
        expired_sets.delete()

        self.stdout.write(
            str.format('{0} expired sets were purged.\n', num_purged)
        )
