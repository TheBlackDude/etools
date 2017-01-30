from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.db.transaction import atomic

from publics.tasks import import_travel_agents


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('xml_path', nargs=1)

    @atomic
    def handle(self, *args, **options):
        xml_path = options['xml_path'][0]

        import_travel_agents(xml_path)
