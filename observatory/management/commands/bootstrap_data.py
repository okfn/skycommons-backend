"""First-run data bootstrap, safe to run on every container start.

Loads the bundled fixture only when the database has no content yet.
Unlike a bare `loaddata`, re-running this never clobbers editor changes.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand

from observatory.models import ContentSection, Country


class Command(BaseCommand):
    help = "Load initial fixtures if (and only if) the database is empty"

    def handle(self, *args, **options):
        if Country.objects.exists() or ContentSection.objects.exists():
            self.stdout.write("bootstrap_data: content present, nothing to do")
            return
        call_command("loaddata", "observatory")
        self.stdout.write(self.style.SUCCESS("bootstrap_data: fixtures loaded"))
