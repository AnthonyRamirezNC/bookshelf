from .test import BaseTestCase
from django.urls import reverse

class UserProfileEndpointsTest(BaseTestCase):
    def setUp(self):
        super().setUp()

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
        recently_liked_book = profile_data["liked_books"][-1]
        assert recently_liked_book["isbn13"] == "9783161484100"