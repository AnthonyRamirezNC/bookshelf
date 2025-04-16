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
import pyisbn
from datetime import datetime
from .cached_book_links import get_link_with_ISBN

#templates
def home(request):
    books = Book.objects.all() 
    return render(request, "index.html", {"books": books})

def book_detail(request, book_id):
    return render(request, "book.html", {"book_id": book_id})

#helper methods
def add_book_to_db(serialized_book):
    #check if book exists based on isbn13 if not add it
    if not check_if_book_in_db(serialized_book):
        Book.objects.create(
            title=serialized_book.get("title"),
            authors=serialized_book.get("authors", []),
            publication_date=serialized_book.get("publication_date"),
            publisher=serialized_book.get("publisher"),
            genres=serialized_book.get("genres", []),
            language=serialized_book.get("language"),
            page_count=serialized_book.get("page_count"),
            isbn=serialized_book.get("isbn"),
        )

def check_if_book_in_db(serialized_book):
    return Book.objects.filter(isbn=serialized_book.get("isbn")).exists()

def normalize_pub_date(pub_date):
    if not pub_date:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(pub_date, fmt).date()
        except ValueError:
            continue
    return None

#external api views

#get book data by title
@extend_schema(
    tags=["External API"],
    request = ExtTitleSerializer, #request serializer to show in docs
    responses= {
            200: OpenApiResponse(description="external Book retrieval by title successful"),
            400: OpenApiResponse(description="Bad Request"),
            500: OpenApiResponse(description="Internal server error"),
        }
    )
@api_view(["GET"])
def ExtGetBooksByTitle(request, title):
    try:
        url = f'https://www.googleapis.com/books/v1/volumes?q={title}&maxResults=40&key={os.getenv("GOOGLE_BOOKS_API_KEY")}'
        ext_response = requests.get(url)
        ext_response_data = ext_response.json()
        book_data_list = ext_response_data["items"]
        serialized_book_list = []
        #serialize each book in the book list
        for book in book_data_list:
            book: dict
            book_info = book["volumeInfo"]

            #extract ISBN13
            if book_info.get("industryIdentifiers"):
                IdentifierList = book_info.get("industryIdentifiers")
                isbn = ""
                for identifier in IdentifierList:
                    #add isbn13
                    if identifier['type'] == 'ISBN_13':
                        isbn = identifier['identifier']
                    #if isbn10 convert to isbn13
                    else:
                        isbn10 = identifier['identifier']
                        if(len(isbn10) == 10):
                            isbn = pyisbn.convert(isbn10)
                
                #extract image if in google books
                if book_info.get("imageLinks"):
                    img_src = book_info["imageLinks"]
                #if not present, search in csv
                else:
                    print("No Image Found for ISBN: ")
                    print(isbn)
                    isbn13 = isbn
                    isbn10 = None
                    if(isbn13[:3] == "978"):
                        isbn10 = pyisbn.convert(isbn13)

                    print("searching csv with both isbn10 and 13 if applicable")
                    
                    cover_img_src = get_link_with_ISBN(isbn13)
                    if(cover_img_src is None and isbn10 is not None):
                        #try with isbn10
                        cover_img_src = get_link_with_ISBN(isbn10)

                    if(cover_img_src is None):
                        print("Cover image not found in cache")
                    
                    
            else:
                continue


            if(len(book_info.get("title")) > 255):
                title = book_info.get("title")[:255]
            else: title = book_info.get("title")

            book_serialized = BookSerializer(data={
                "title": title,
                "authors": book_info.get("authors", []),
                "publication_date": normalize_pub_date(book_info.get("publishedDate")),
                "publisher": book_info.get("publisher", "Unknown"),
                "genres": book_info.get("categories", []),
                "language": book_info.get("language"),
                "page_count": book_info.get("pageCount"),
                "isbn13" : isbn,
                "img_src" : img_src['thumbnail']
            })
            if book_serialized.is_valid():
                serialized_book_list.append(book_serialized.data)
            else: 
                print("could not serialize book because: \n")
                print(book_serialized.errors)

            message = f'Ext Call for title: {title} Successful'
        return Response({
            'message': message,
            'num_books_returned' : len(serialized_book_list),
            'books_returned' : serialized_book_list,
            }, status=status.HTTP_200_OK)
    except Exception as e:
        if str(e) == "'items'":
            return Response({
            'message': f'Ext Call for title: {title} Successful but no results returned',
            }, status=status.HTTP_200_OK)
        else:
            return Response({
            'message': "An internal error occured",
            'error' : str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@extend_schema(
    tags=["External API"],
    request = ExtGenreSerializer, #request serializer to show in docs
    responses= {
            200: OpenApiResponse(description="external Book retrieval by genre successful"),
            400: OpenApiResponse(description="Bad Request"),
            500: OpenApiResponse(description="Internal server error"),
        }
    )
@api_view(["GET"])
def ExtGetBooksByGenre(request, genre):
    try:
        url = f'https://www.googleapis.com/books/v1/volumes?q=subject:{genre}&maxResults=40&key={os.getenv("GOOGLE_BOOKS_API_KEY")}'
        ext_response = requests.get(url)
        ext_response_data = ext_response.json()
        book_data_list = ext_response_data["items"]
        serialized_book_list = []
        for book in book_data_list:
            book: dict
            book_info = book["volumeInfo"]

            if book_info.get("industryIdentifiers"):
                IdentifierList = book_info.get("industryIdentifiers")
                isbn = ""
                for identifier in IdentifierList:
                    if identifier['type'] == 'ISBN_13':
                        isbn = identifier['identifier']
            else:
                continue
            
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
            message = f'Ext Call for genre: {genre} Successful'
        return Response({
            'message': message,
            'num_books_returned' : len(serialized_book_list),
            'books_returned' : serialized_book_list,
            }, status=status.HTTP_200_OK)
    except Exception as e:
        if str(e) == "'items'":
            return Response({
            'message': f'Ext Call for Genre: {genre} Successful but no results returned',
            }, status=status.HTTP_200_OK)
        else:
            return Response({
            'message': "An internal error occured",
            'error' : str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=["External API"],
    request = ExtAuthorSerializer, #request serializer to show in docs
    responses= {
            200: OpenApiResponse(description="external Book retrieval by author successful"),
            400: OpenApiResponse(description="Bad Request"),
            500: OpenApiResponse(description="Internal server error"),
        }
    )
@api_view(["GET"])
def ExtGetBooksByAuthor(request, author):
    try:
        url = f'https://www.googleapis.com/books/v1/volumes?q=inauthor:{author}&maxResults=40&key={os.getenv("GOOGLE_BOOKS_API_KEY")}'
        
        ext_response = requests.get(url)
        ext_response_data = ext_response.json()
        if ext_response_data["items"]:
            book_data_list = ext_response_data["items"]
            serialized_book_list = []
            for book in book_data_list:
                book: dict
                book_info = book["volumeInfo"]

                if book_info.get("industryIdentifiers"):
                    IdentifierList = book_info.get("industryIdentifiers")
                    isbn = ""
                    for identifier in IdentifierList:
                        if identifier['type'] == 'ISBN_13':
                            isbn = identifier['identifier']
                else: 
                    continue
                
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
                message = f'Ext Call for author: {author} Successful'
        else: 
            message = f'Ext Call for Author: {author} Successful But no results returned'
        return Response({
            'message': message,
            'num_books_returned' : len(serialized_book_list),
            'books_returned' : serialized_book_list,
            }, status=status.HTTP_200_OK)
    except Exception as e:
        if str(e) == "'items'":
            return Response({
            'message': f'Ext Call for author: {author} Successful but no results returned',
            }, status=status.HTTP_200_OK)
        else:
            return Response({
            'message': "An internal error occured",
            'error' : str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=["External API"],
    request = ExtISBNSerializer, #request serializer to show in docs
    responses= {
            200: OpenApiResponse(description="external Book retrieval by isbn successful"),
            400: OpenApiResponse(description="Bad Request"),
            500: OpenApiResponse(description="Internal server error"),
        }
    )
@api_view(["GET"])
def ExtGetBooksByIsbn(request, isbn):
    try:
        url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&maxResults=40&key={os.getenv("GOOGLE_BOOKS_API_KEY")}'
        
        ext_response = requests.get(url)
        ext_response_data = ext_response.json()
        if ext_response_data["items"]:
            book_data_list = ext_response_data["items"]
            serialized_book_list = []
            for book in book_data_list:
                book: dict
                book_info = book["volumeInfo"]

                if book_info.get("industryIdentifiers"):
                    IdentifierList = book_info.get("industryIdentifiers")
                    isbn = ""
                    for identifier in IdentifierList:
                        if identifier['type'] == 'ISBN_13':
                            isbn = identifier['identifier']
                else: 
                    continue
                
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
                message = f'Ext Call for isbn: {isbn} Successful'
        else: 
            message = f'Ext Call for isbn: {isbn} Successful But no results returned'
        return Response({
            'message': message,
            'num_books_returned' : len(serialized_book_list),
            'books_returned' : serialized_book_list,
            }, status=status.HTTP_200_OK)
    except Exception as e:
        if str(e) == "'items'":
            return Response({
            'message': f'Ext Call for isbn: {isbn} Successful but no results returned',
            }, status=status.HTTP_200_OK)
        else:
            return Response({
            'message': "An internal error occured",
            'error' : str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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