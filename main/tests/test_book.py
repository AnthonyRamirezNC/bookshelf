from .test import BaseTestCase
from django.urls import reverse
import uuid

#External API endpoints



#Internal API endpoints

#test api endpoint
class BookTitleEndpointTest(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_ext_book_get(self):
        url = reverse("ext-books-by-title", kwargs={"title": "Dune"})
        response = self.user_client.get(url)
        
