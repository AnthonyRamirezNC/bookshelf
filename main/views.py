from django.shortcuts import render, redirect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from rest_framework.decorators import api_view, permission_classes
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
            isbn13=serialized_book.get("isbn13"),
            publication_date=serialized_book.get("publication_date"),
            publisher=serialized_book.get("publisher"),
            genres=serialized_book.get("genres", []),
            language=serialized_book.get("language"),
            page_count=serialized_book.get("page_count"),
            img_src=serialized_book.get("img_src")
        ) 

def check_if_book_in_db(serialized_book):
    return Book.objects.filter(isbn13=serialized_book.get("isbn13")).exists()

def normalize_pub_date(pub_date):
    if not pub_date:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(pub_date, fmt).date()
        except ValueError:
            continue
    return None

def serialize_books_from_ext_response(book_data_list):
    serialized_book_list = []
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
                    isbn = identifier['identifier'].replace("-", "")
                #if isbn10 convert to isbn13
                else:
                    isbn10 = identifier['identifier'].replace("-", "")
                    if(len(isbn10) == 10):
                        isbn = pyisbn.convert(isbn10)
            
            #extract image if in google books
            if book_info.get("imageLinks"):
                img_src = book_info["imageLinks"]
                src_link = img_src['thumbnail']
            #if not present, search in csv
            else:
                #No Image Found for ISBN
                isbn13 = isbn
                isbn10 = None
                if(isbn13[:3] == "978"):
                    isbn10 = pyisbn.convert(isbn13)
                #searching csv with both isbn10 and 13 if applicable
                src_link = get_link_with_ISBN(isbn13)
                if(src_link is None and isbn10 is not None):
                    #try with isbn10
                    src_link = get_link_with_ISBN(isbn10)
        else:
            continue

        if(len(book_info.get("title")) > 255):
            title = book_info.get("title")[:255]
        else: title = book_info.get("title")

        if(src_link is None):
            #Cover image not found
            src_link = "Missing"

        book_serialized = BookSerializer(data={
            "title": title,
            "authors": book_info.get("authors", []),
            "publication_date": normalize_pub_date(book_info.get("publishedDate")),
            "publisher": book_info.get("publisher", "Unknown"),
            "genres": book_info.get("categories", []),
            "language": book_info.get("language"),
            "page_count": book_info.get("pageCount"),
            "isbn13" : isbn,
            "img_src" : src_link
        })
        if book_serialized.is_valid():
            serialized_book_list.append(book_serialized.data)
        else: 
            print("could not serialize book because: \n")
            print(book_serialized.errors)
    return serialized_book_list

def create_book_item(isbn):
    url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&maxResults=1&key={os.getenv("GOOGLE_BOOKS_API_KEY")}'
    ext_response = requests.get(url)
    ext_response_data = ext_response.json()

    if "items" not in ext_response_data:
        return None

    book_data_list = ext_response_data["items"]
    serialized_books = serialize_books_from_ext_response(book_data_list)

    if not serialized_books:
        return None

    book_data = serialized_books[0]
    try:
        book = Book.objects.create(**book_data)
        return book
    except Exception as e:
        return None

#external api views

#get book data by title
@extend_schema(
    tags=["External API"],
    request = ExtTitleSerializer, #request serializer to show in docs
    responses= {
            200: OpenApiResponse(description="external Book retrieval by title successful"),
            500: OpenApiResponse(description="Internal server error"),
        }
    )
@api_view(["GET"])
def ExtGetBooksByTitle(request, title):
    try:
        url = f'https://www.googleapis.com/books/v1/volumes?q=intitle:{title}&maxResults=40&key={os.getenv("GOOGLE_BOOKS_API_KEY")}'
        ext_response = requests.get(url)
        ext_response_data = ext_response.json()
        book_data_list = ext_response_data["items"]
        #serialize each book in the book list
        serialized_book_list = serialize_books_from_ext_response(book_data_list)
        return Response({
            'message': f'Ext Call for title: {title} Successful',
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
        #serialize each book in the book list
        serialized_book_list = serialize_books_from_ext_response(book_data_list)
        
        return Response({
            'message': f'Ext Call for Genre: {genre}',
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
            500: OpenApiResponse(description="Internal server error"),
        }
    )
@api_view(["GET"])
def ExtGetBooksByAuthor(request, author):
    try:
        url = f'https://www.googleapis.com/books/v1/volumes?q=inauthor:{author}&maxResults=40&key={os.getenv("GOOGLE_BOOKS_API_KEY")}'
        ext_response = requests.get(url)
        ext_response_data = ext_response.json()
        book_data_list = ext_response_data["items"]
        #serialize each book in the book list
        serialized_book_list = serialize_books_from_ext_response(book_data_list)
        
        return Response({
            'message': f'Ext Call for Author: {author} Successful',
            'num_books_returned' : len(serialized_book_list),
            'books_returned' : serialized_book_list,
            }, status=status.HTTP_200_OK)
    except Exception as e:
        if str(e) == "'items'":
            return Response({
            'message': f'Ext Call for Author: {author} Successful but no results returned',
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
            500: OpenApiResponse(description="Internal server error"),
        }
    )
@api_view(["GET"])
def GetBooksByIsbn(request, isbn):
    isbn = isbn.replace("-", "")
    try:
        book = Book.objects.get(isbn13=isbn)
        serialized_book = BookSerializer(book).data
        return Response({
                'message': f'call for ISBN: {isbn} Successful',
                'books_returned' : [serialized_book],
                }, status=status.HTTP_200_OK)

    except Book.DoesNotExist:
        try:
            url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&maxResults=40&key={os.getenv("GOOGLE_BOOKS_API_KEY")}'
            ext_response = requests.get(url)
            ext_response_data = ext_response.json()
            book_data_list = ext_response_data["items"]
            #serialize each book in the book list
            serialized_book_list = serialize_books_from_ext_response(book_data_list)
            
            return Response({
                'message': f'call for ISBN: {isbn} Successful',
                'num_books_returned' : len(serialized_book_list),
                'books_returned' : serialized_book_list,
                }, status=status.HTTP_200_OK)
        except Exception as e:
            if str(e) == "'items'":
                return Response({
                'message': f'Ext Call for ISBN: {isbn} Successful but no results returned',
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
            200: OpenApiResponse(description="Book Retrieval successful")
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


#User Profile endpoints

#get User Profile based on user
@extend_schema(
tags=["User Profile"],
responses= {
        200: OpenApiResponse(description="external Book retrieval by title successful"),
        400: OpenApiResponse(description="Bad Request"),
        403: OpenApiResponse(description="Forbidden, Authentication likely not provided"),
        404: OpenApiResponse(description="User Profile Not Found"),
        500: OpenApiResponse(description="Internal server error"),
    }
) 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users_profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        serialized_profile = UserProfileSerializer(user_profile)
        return Response({
        "message" : "User Profile Found",
        "profile_data" : serialized_profile.data
        })
    except UserProfile.DoesNotExist:
        return Response({"error": "User Profile not found"}, status=404)


@extend_schema(
tags=["User Profile"],
responses= {
        200: OpenApiResponse(description="external Book retrieval by title successful"),
        400: OpenApiResponse(description="Bad Request"),
        403: OpenApiResponse(description="Forbidden, Authentication likely not provided"),
        404: OpenApiResponse(description="User Profile Not Found"),
        500: OpenApiResponse(description="Internal server error"),
    }
) 
#like book based on isbn
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_book_with_isbn(request, isbn):
    isbn = isbn.replace("-", "")
    if len(isbn) == 10:
        isbn = pyisbn.convert(isbn)

    try:
        # Try to get book locally
        book = Book.objects.get(isbn13=isbn)
    except Book.DoesNotExist:
        # Query Google Books API
        url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&maxResults=1&key={os.getenv("GOOGLE_BOOKS_API_KEY")}'
        ext_response = requests.get(url)
        ext_response_data = ext_response.json()

        if "items" not in ext_response_data:
            return Response({"error": "No books found with that ISBN"}, status=404)

        book_data_list = ext_response_data["items"]
        serialized_books = serialize_books_from_ext_response(book_data_list)

        if not serialized_books:
            return Response({"error": "Failed to process external book data"}, status=400)

        book_data = serialized_books[0]
        try:
            book = Book.objects.create(**book_data)
        except Exception as e:
            return Response({"error": f"Failed to create book: {str(e)}"}, status=500)

    # Add book to liked_books
    user_profile = UserProfile.objects.get(user=request.user)
    user_profile.liked_books.add(book)

    return Response({"message": "Book liked!"})

@extend_schema(
tags=["User Profile"],
request = UserProfileSerializer, #request serializer to show in docs
responses= {
        200: OpenApiResponse(description="external Book retrieval by title successful"),
        400: OpenApiResponse(description="Bad Request"),
        403: OpenApiResponse(description="Forbidden, Authentication likely not provided"),
        404: OpenApiResponse(description="User Profile Not Found"),
        500: OpenApiResponse(description="Internal server error"),
    }
)
#update user profile
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = UserProfileSerializer(instance=user_profile, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "User profile updated successfully.",
            "profile": serializer.data
        }, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#create user profile
@extend_schema(
tags=["User Profile"],
request = UserProfileSerializer, #request serializer to show in docs
responses= {
        200: OpenApiResponse(description="external Book retrieval by title successful"),
        400: OpenApiResponse(description="Bad Request"),
        403: OpenApiResponse(description="Forbidden, Authentication likely not provided"),
        500: OpenApiResponse(description="Internal server error"),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_user_profile(request):
    user = request.user

    # Check if the profile already exists
    if UserProfile.objects.filter(user=user).exists():
        return Response({
            "message" : "User Profile already exists",
        })
 
    serializer = UserProfileSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=user)
        return Response({
            "message": "User profile created successfully.",
            "profile": serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#Review Endpoints

#create review
@extend_schema(
    tags=["Reviews"],
    request=ReviewSerializer,
    responses={
        201: OpenApiResponse(description="Review created successfully"),
        400: OpenApiResponse(description="Bad Request"),
        403: OpenApiResponse(description="Forbidden, Authentication likely not provided"),
        404: OpenApiResponse(description="User profile or Book not found"),
        500: OpenApiResponse(description="Internal server error"),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review_with_isbn(request, isbn):
    isbn = isbn.replace("-", "")
    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            book = Book.objects.get(isbn13=isbn)
        except Book.DoesNotExist:
            book=create_book_item(isbn)
            if book is None:
                return Response({
                "message": "Book with that isbn could not be found or created",
            }, status=status.HTTP_404_NOT_FOUND)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)

        # Prevent duplicate reviews
        if Review.objects.filter(user_profile=user_profile, book=book).exists():
            return Response({
                "error": "Review already exists for this book by the user, call edit endpoint instead."
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(user_profile=user_profile, book=book)
        return Response({
            "message": "Review created successfully.",
            "review": serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=["Reviews"],
    request=ReviewSerializer,
    responses={
        201: OpenApiResponse(description="Review created successfully"),
        400: OpenApiResponse(description="Bad Request"),
        403: OpenApiResponse(description="Forbidden, Authentication likely not provided"),
        404: OpenApiResponse(description="User profile or Book not found"),
        500: OpenApiResponse(description="Internal server error"),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_review_with_isbn(request, isbn):
    isbn = isbn.replace("-", "")
    try:
        if not isbn:
            return Response({"error": "ISBN is required."}, status=status.HTTP_400_BAD_REQUEST)

        user_profile = UserProfile.objects.get(user=request.user)
        book = Book.objects.get(isbn13=isbn)
        review = Review.objects.get(book=book, user_profile=user_profile)

    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)
    except Book.DoesNotExist:
        return Response({"error": "Book not found with that ISBN."}, status=status.HTTP_404_NOT_FOUND)
    except Review.DoesNotExist:
        return Response({"error": "Trying to edit review that doesn't exist. Create one first."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ReviewSerializer(instance=review, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Review updated successfully.",
            "review": serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
@extend_schema(
    tags=["Reviews"],
    request=ExtISBNSerializer,
    responses={
        200: OpenApiResponse(
            response=UserReviewSerializer(many=True),
            description="List of reviews for the book."
        ),
        400: OpenApiResponse(description="Bad Request"),
        404: OpenApiResponse(description="Book not found"),
        500: OpenApiResponse(description="Internal server error"),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_reviews_by_isbn(request, isbn):
    isbn = isbn.replace("-", "")
    try:
        book = Book.objects.get(isbn13=isbn)
    except Book.DoesNotExist:
        book=create_book_item(isbn)
        if book is None:
            return Response({
            "message": "Book with that isbn could not be found or created",
        }, status=status.HTTP_404_NOT_FOUND)

    reviews = Review.objects.filter(book=book)

    serialized = UserReviewSerializer(reviews, many=True)
    review_list = []

    for review_data in serialized.data:
        review_data["isbn13"] = isbn
        review_list.append(review_data)

    return Response({
        "message": f"Found {len(reviews)} reviews for the book.",
        "reviews": review_list
    }, status=status.HTTP_200_OK)

@extend_schema(
    tags=["Reviews"],
    responses={
        200: OpenApiResponse(
            response=UserReviewSerializer(many=True),
            description="List of reviews made by the user."
        ),
        400: OpenApiResponse(description="Bad Request"),
        403: OpenApiResponse(description="Authentication error, User not logged in"),
        404: OpenApiResponse(description="Book not found"),
        500: OpenApiResponse(description="Internal server error"),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_reviews_by_user(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found, may need to login."}, status=status.HTTP_404_NOT_FOUND)

    reviews = Review.objects.filter(user_profile=user_profile)
    serializer = UserReviewSerializer(reviews, many=True)

    return Response({
        "message": f"Found {len(reviews)} reviews for the User.",
        "reviews": serializer.data
    }, status=status.HTTP_200_OK)
