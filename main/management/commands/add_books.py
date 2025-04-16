from django.core.management.base import BaseCommand
from bookshelf.scripts.addBooksByLetter import addBooksByLetter

class Command(BaseCommand):
    help = 'Fetches books by first letter and adds one to the DB'

    def handle(self, *args, **kwargs):
        addBooksByLetter()
        self.stdout.write(self.style.SUCCESS("Books added to DB successfully"))
