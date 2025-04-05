from django.shortcuts import render, redirect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Book
from .serializers import *
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from rest_framework.decorators import api_view
import requests
import os

#templates
def home(request):
    books = Book.objects.all() 
    return render(request, "index.html", {"books": books})

def book_detail(request, book_id):
    return render(request, "book.html", {"book_id": book_id})

#external api views

#get book data by genre
@extend_schema(
    tags=["External API"],
    request = ExtGenreSerializer, #request serializer to show in docs
    responses= {
            200: OpenApiResponse(description="external Book retrieval by title successful"),
            400: OpenApiResponse(description="Bad Request"),
        }
    )
@api_view(["GET"])
def ExtGetBooksByTitle(request, title):
    url = f'https://www.googleapis.com/books/v1/volumes?q=intitle:{title}&maxResults=20&key={os.getenv("GOOGLE_BOOKS_API_KEY")}'
    
    ext_response = requests.get(url)
    ext_response_data = ext_response.json()
    book_data_list = ext_response_data["items"]
    serialized_book_list = []
    for book in book_data_list:
        book: dict
        book_info = book["volumeInfo"]

        IdentifierList = book_info.get("industryIdentifiers")
        isbn = ""
        for identifier in IdentifierList:
            if identifier['type'] == 'ISBN_13':
                isbn = identifier['identifier']
        
        book_serialized = BookSerializer(data={
            "title": book_info.get("title"),
            "authors": book_info.get("authors", []),
            "publication_date": book_info.get("publishedDate"),
            "publisher": book_info.get("publisher"),
            "genres": book_info.get("categories", []),
            "language": book_info.get("language"),
            "page_count": book_info.get("pageCount"),
            "isbn" : isbn,
        })
        if book_serialized.is_valid():
            serialized_book_list.append(book_serialized.data)
    return Response({
        'message': f'Ext Call for title: {title} Successful',
        'num_books_returned' : len(book_data_list),
        'books_returned' : serialized_book_list,
        }, status=status.HTTP_200_OK)

@api_view(["GET"])
def ExtGetBooksByGenre(request, genre):
    url = f'https://www.googleapis.com/books/v1/volumes?q=subject:{genre}&maxResults=20&key={os.getenv("GOOGLE_BOOKS_API_KEY")}'
    
    ext_response = requests.get(url)
    ext_response_data = ext_response.json()
    book_data_list = ext_response_data["items"]
    serialized_book_list = []
    for book in book_data_list:
        book: dict
        book_info = book["volumeInfo"]

        IdentifierList = book_info.get("industryIdentifiers")
        isbn = ""
        for identifier in IdentifierList:
            if identifier['type'] == 'ISBN_13':
                isbn = identifier['identifier']
        
        book_serialized = BookSerializer(data={
            "title": book_info.get("title"),
            "authors": book_info.get("authors", []),
            "publication_date": book_info.get("publishedDate"),
            "publisher": book_info.get("publisher"),
            "genres": book_info.get("categories", []),
            "language": book_info.get("language"),
            "page_count": book_info.get("pageCount"),
            "isbn" : isbn,
        })
        if book_serialized.is_valid():
            serialized_book_list.append(book_serialized.data)
    return Response({
        'message': f'Ext Call for genre: {genre} Successful',
        'num_books_returned' : len(book_data_list),
        'books_returned' : serialized_book_list,
        }, status=status.HTTP_200_OK)


@api_view(["GET"])
def ExtGetBooksByAuthor(request, author):
    url = f'https://www.googleapis.com/books/v1/volumes?q=inauthor:{author}&maxResults=20&key={os.getenv("GOOGLE_BOOKS_API_KEY")}'
    
    ext_response = requests.get(url)
    ext_response_data = ext_response.json()
    book_data_list = ext_response_data["items"]
    serialized_book_list = []
    for book in book_data_list:
        book: dict
        book_info = book["volumeInfo"]

        IdentifierList = book_info.get("industryIdentifiers")
        isbn = ""
        for identifier in IdentifierList:
            if identifier['type'] == 'ISBN_13':
                isbn = identifier['identifier']
        
        book_serialized = BookSerializer(data={
            "title": book_info.get("title"),
            "authors": book_info.get("authors", []),
            "publication_date": book_info.get("publishedDate"),
            "publisher": book_info.get("publisher"),
            "genres": book_info.get("categories", []),
            "language": book_info.get("language"),
            "page_count": book_info.get("pageCount"),
            "isbn" : isbn,
        })
        if book_serialized.is_valid():
            serialized_book_list.append(book_serialized.data)
    return Response({
        'message': f'Ext Call for author: {author} Successful',
        'num_books_returned' : len(book_data_list),
        'books_returned' : serialized_book_list,
        }, status=status.HTTP_200_OK)

@api_view(["GET"])
def ExtGetBooksByIsbn(request, isbn_query):
    url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn_query}&maxResults=20&key={os.getenv("GOOGLE_BOOKS_API_KEY")}'
    
    ext_response = requests.get(url)
    ext_response_data = ext_response.json()
    book_data_list = ext_response_data["items"]
    serialized_book_list = []
    for book in book_data_list:
        book: dict
        book_info = book["volumeInfo"]

        IdentifierList = book_info.get("industryIdentifiers")
        isbn = ""
        for identifier in IdentifierList:
            if identifier['type'] == 'ISBN_13':
                isbn = identifier['identifier']
        
        book_serialized = BookSerializer(data={
            "title": book_info.get("title"),
            "authors": book_info.get("authors", []),
            "publication_date": book_info.get("publishedDate"),
            "publisher": book_info.get("publisher"),
            "genres": book_info.get("categories", []),
            "language": book_info.get("language"),
            "page_count": book_info.get("pageCount"),
            "isbn" : isbn,
        })
        if book_serialized.is_valid():
            serialized_book_list.append(book_serialized.data)
    return Response({
        'message': f'Ext Call for isbn: {isbn_query} Successful',
        'num_books_returned' : len(book_data_list),
        'books_returned' : serialized_book_list,
        }, status=status.HTTP_200_OK)

#database views


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("/")
    else:
        form = AuthenticationForm()
    
    return render(request, "login.html", {"form": form})

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")
    else:
        form = CustomUserCreationForm()

    return render(request, "register.html", {"form": form})



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