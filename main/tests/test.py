from django.test import TestCase
from django.urls import reverse
from main.models import *
import uuid

#create base class, will use this for each custom test class
class BaseTestCase(TestCase):
    def setUp(self):
        #create example django user
        self.example_user = User.objects.create(
            first_name = "John",
            last_name = "Doe",
            username = "john_doe",
            email="john@example.com",
            password="securepassword123"
        )

        #create a user profile
        self.example_user_profile = UserProfile.objects.create(
            user = self.example_user,
            bio = "This is an example bio for John Doe"
        )

        # Create an authenticated client for the user with djangos default client
        self.user_client = self.client
        self.user_client.login(username="john_doe", password="securepassword123")

        #create example book object to test with
        self.example_book = Book.objects.create(
            id=uuid.uuid4(),
            title="The Great Adventure",
            authors=["John Doe", "Jane Smith"],
            isbn="978-3-16-148410-0",
            publication_date="2023-05-10",
            publisher="Epic Books Publishing",
            genres=["Adventure", "Fantasy"],
            language="English",
            page_count=350
        )