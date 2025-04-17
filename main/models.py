from django.db import models
import uuid
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField

class Book(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    authors = models.JSONField(blank=True, null=True, default=list)
    isbn13 = models.CharField(max_length=20, unique=True, blank=True, null=True)
    publication_date = models.DateField(blank=True, null=True)
    publisher = models.CharField(max_length=255, blank=True, null=True)
    genres = models.JSONField(blank=True, null=True, default=list)
    language = models.CharField(max_length=50, blank=True, null=True)
    page_count = models.IntegerField(blank=True, null=True)
    img_src = models.CharField(max_length=255, default="Missing", blank=True, null=True)
    class Meta:
        db_table = "api_book"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    liked_books = models.ManyToManyField(Book, blank=True)

    class Meta:
        db_table = "api_user_profile"

