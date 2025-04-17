from django.apps import AppConfig
import pandas as pd


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        from . import cached_book_links  # Import to trigger load
        cached_book_links.load_df()
