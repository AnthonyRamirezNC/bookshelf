from django.core.management.base import BaseCommand
from bookshelf.scripts.normalizeGenres import normalizeGenres

class Command(BaseCommand):
    help = 'Fetches books from DB and normalize genres'

    def handle(self, *args, **kwargs):
        normalizeGenres()
        self.stdout.write(self.style.SUCCESS("Books normalized to DB successfully"))