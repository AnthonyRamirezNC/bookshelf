"""
URL configuration for djangoTemplate project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.contrib.auth import views as auth_views
from main.views import *
from main.views import book_detail

urlpatterns = [
    # Schema endpoint
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # Swagger UI
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    path('admin/', admin.site.urls),
    
    #templates
    path("", home, name="home"),

    #Books
    path("books/", BookListCreateView.as_view(), name="book-list-create"),

    path("books/<uuid:book_id>/", BookDetailView.as_view(), name="book-detail"),

    path("login/", login_view, name="login"),
    path("register/", register, name="register"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    #user profiles
    path("user/profile", get_users_profile, name="get-user-profile"),
    path("user/profile/like-book-isbn/<str:isbn>", like_book_with_isbn, name="like-book-by-isbn"),
    path("user/profile/edit", update_user_profile, name="edit-user-profile"),
    path("user/profile/create", create_user_profile, name = "create-user-profile"),

    #external books apis
    path("ext/books/search-title/<str:title>", ExtGetBooksByTitle, name="ext-books-by-title"),
    path("ext/books/search-genre/<str:genre>", ExtGetBooksByGenre, name="ext-books-by-genre"),
    path("ext/books/search-author/<str:author>", ExtGetBooksByAuthor, name="ext-books-by-author"),
    path("ext/books/search-isbn/<str:isbn>", ExtGetBooksByIsbn, name="ext-books-by-isbn"),

    path("book/<str:book_id>/", book_detail, name="book-detail"),
]
