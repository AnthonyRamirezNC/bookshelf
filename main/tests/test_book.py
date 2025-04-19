from .test import BaseTestCase
from django.urls import reverse
import uuid
from rest_framework import status

#External API endpoints



#Internal API endpoints

#test external api endpoint
class BookTitleEndpointTest(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_ext_book_get(self):
        url = reverse("ext-books-by-title", kwargs={"title": "Dune"})
        response = self.user_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
class BookGenreEndpointTest(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_ext_book_get(self):
        url = reverse("ext-books-by-genre", kwargs={"genre": "Horror"})
        response = self.user_client.get(url)
        # print("Genre Response:\n" + str(response.json()))
        assert response.status_code == status.HTTP_200_OK


class BookAuthorEndpointTest(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_ext_book_get(self):
        url = reverse("ext-books-by-author", kwargs={"author": "Robert Kirkman"})
        response = self.user_client.get(url)
        # print("Author Response", response.json())
        assert response.status_code == status.HTTP_200_OK


class BookIsbnEndpointTest(BaseTestCase):
     def setUp(self):
        super().setUp()

     def test_ext_book_get(self):
        isbn = "978-3-16-148410-0"
        url = reverse("ext-books-by-isbn", kwargs={"isbn": isbn})
        response = self.user_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "message" in data
        assert "books_returned" in data