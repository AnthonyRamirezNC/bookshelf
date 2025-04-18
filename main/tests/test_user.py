from .test import BaseTestCase
from django.urls import reverse
from django.test import Client
from ..models import *

class UserProfileEndpointsTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create second example user
        self.example_user_2 = User.objects.create_user(
            first_name="Jane",
            last_name="Doe",
            username="jane_doe",
            email="jane@example.com",
            password="password1"
        )

        self.user_client_2 = Client()
        self.user_client_2.login(username="jane_doe", password="password1")
    
    #test creating user profile
    def test_create_user_profile(self):
        url = reverse("create-user-profile")
        data = {
            "bio": "new Bio",
            "display_name": "test_name"
        }
        response = self.user_client_2.post(url, data)
        
        assert response.status_code == 201

        #assert profile was created
        assert UserProfile.objects.filter(user=self.example_user_2).exists()
        user_profile = UserProfile.objects.get(user=self.example_user_2)
        assert user_profile.bio == "new Bio"
        assert user_profile.display_name == "test_name"


    #test getting user profile
    def test_get_user_profile(self):
        url = reverse("get-user-profile")
        response = self.user_client.get(url)
        response_data = response.data

        #assert profile fields were created
        assert response_data["message"] == "User Profile Found"
        profile_data =  response_data["profile_data"]
        assert profile_data["bio"] == "This is an example bio for John Doe"
        assert profile_data["display_name"] == "johndoethebro"

    #test adding a book to liked books with ISBN
    def test_like_book_with_isbn(self):
        url = reverse("like-book-by-isbn", kwargs={"isbn" : "9783161484100"})
        response = self.user_client.post(url)
        assert response.status_code == 200
    
        #check if user profile was updated
        url = reverse("get-user-profile")
        response = self.user_client.get(url)
        response_data = response.data
        profile_data =  response_data["profile_data"]
        # print("Liked Books: \n ")
        # print(profile_data["liked_books"])
        recently_liked_book = profile_data["liked_books"][-1]
        assert recently_liked_book["isbn13"] == "9783161484100"