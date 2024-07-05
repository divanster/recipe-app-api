# core/management/commands/list_urls.py

from django.core.management.base import BaseCommand
from django.urls import get_resolver


class Command(BaseCommand):
    help = 'List all registered URLs'

    def handle(self, *args, **options):
        resolver = get_resolver()
        for url_pattern in resolver.url_patterns:
            print(url_pattern)
