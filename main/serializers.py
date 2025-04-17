from rest_framework import serializers
from main.models import *
import uuid

#book
class BookSerializer(serializers.Serializer):
    id = serializers.UUIDField(default=uuid.uuid4, read_only=True)
    title = serializers.CharField(max_length=255)
    authors = serializers.ListField(
        child=serializers.CharField(max_length=255),
        allow_empty=True,
        required=False
    )
    isbn13 = serializers.CharField(max_length=20, allow_blank=True, required=False)
    publication_date = serializers.DateField(required=False, allow_null=True)
    publisher = serializers.CharField(max_length=255, allow_blank=True, required=False)

    genres = serializers.ListField(
        child=serializers.CharField(max_length=255),
        allow_empty=True,
        required=False
    )
    language = serializers.CharField(max_length=50, allow_blank=True, required=False)
    page_count = serializers.IntegerField(required=False, allow_null=True)
    img_src = serializers.CharField(allow_blank = True, required=False)

#User Profile
class UserProfileSerializer(serializers.ModelSerializer):
    liked_books = BookSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = ["bio", "display_name", "liked_books"]


#external api serializers
class ExtGenreSerializer(serializers.Serializer):
    genre = serializers.CharField(max_length = 50)

class ExtTitleSerializer(serializers.Serializer):
    title = serializers.CharField(max_length = 50)

class ExtISBNSerializer(serializers.Serializer):
    isbn = serializers.CharField(max_length = 50)

class ExtAuthorSerializer(serializers.Serializer):
    author = serializers.CharField(max_length = 50)