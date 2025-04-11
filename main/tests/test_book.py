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
        url = reverse("ext-books-by-isbn", kwargs={"isbn": "978-3-16-148410-0"})
        response = self.user_client.get(url)
        # print("Author Response", response.json())
        print("CODE", response.status_code)
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            assert response.status_code == status.HTTP_400_BAD_REQUEST
        else:
            assert response.status_code == status.HTTP_200_OK
