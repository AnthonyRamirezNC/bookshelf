from rest_framework import serializers
from main.models import Book

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = "__all__"  # Include all fields in the Book model
