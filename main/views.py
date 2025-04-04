from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Book
from .serializers import BookSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse

#templates
def home(request):
    books = Book.objects.all() 
    return render(request, "index.html", {"books": books})

def book_detail(request, book_id):
    return render(request, "book.html", {"book_id": book_id})

#books
@extend_schema(tags=["Books"])
class BookListCreateView(APIView):
    """Handles GET (list all books) and POST (create a new book)"""
    @extend_schema(
        request=BookSerializer(many=True),
        responses={
            200: OpenApiResponse(description="Book Retrieval successful"),
            400: OpenApiResponse(description="Bad Request"),
        },
    )
    def get(self, request):
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        request=BookSerializer(many=True),
        responses={
            201: OpenApiResponse(description="Book created successfully"),
            400: OpenApiResponse(description="Bad Request"),
        },
    )
    def post(self, request):
        serializer = BookSerializer(many=True, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(tags=["Books"])
class BookDetailView(APIView):
    """Handles GET (retrieve), PUT (update), and DELETE (remove)"""
    
    def get_object(self, book_id):
        try:
            return Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return None

    @extend_schema(
        request=BookSerializer(),
        responses={
            200: OpenApiResponse(description="Book Retreival by id successful"),
            400: OpenApiResponse(description="Bad Request"),
        },
    )
    def get(self, request, book_id):
        book = self.get_object(book_id)
        if book is None:
            return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = BookSerializer(book)
        return Response(serializer.data)
    
    #create new 
    @extend_schema(
        request=BookSerializer(),
        responses={
            201: OpenApiResponse(description="Book Retreival by id successful"),
            400: OpenApiResponse(description="Bad Request"),
        },
    )
    def put(self, request, book_id):
        book = self.get_object(book_id)
        if book is None:
            return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = BookSerializer(book, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, book_id):
        book = self.get_object(book_id)
        if book is None:
            return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)
        book.delete()
        return Response({"message": "Book deleted successfully"}, status=status.HTTP_204_NO_CONTENT)