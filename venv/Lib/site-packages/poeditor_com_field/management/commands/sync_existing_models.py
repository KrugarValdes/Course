from django.core.management.base import BaseCommand
from poeditor_com_field.core import sync_existing_models


class Command(BaseCommand):
    help = 'Tries to send all existing database fields to the server.'

    def handle(self, *args, **kwargs):
        sync_existing_models()
