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

    def test_follow_and_unfollow_user(self):
        UserProfile.objects.create(
            user = self.example_user_2,
            bio = "This is an example bio for Jane Doe",
            display_name = "janedoesbro"
        )

        profile_1 = UserProfile.objects.get(user=self.example_user)
        profile_2 = UserProfile.objects.get(user=self.example_user_2)

        # Follow user 2 from user 1
        url = reverse("follow-user", kwargs={"target_username": "jane_doe"})
        response = self.user_client.post(url)
        assert response.status_code == 200
        assert profile_2 in profile_1.followed_users.all()

        # Try to follow again — should fail
        response = self.user_client.post(url)
        assert response.status_code == 400
        assert "already following" in response.data["detail"].lower()

        # Try to follow self — should fail
        url_self = reverse("follow-user", kwargs={"target_username": "john_doe"})
        response = self.user_client.post(url_self)
        assert response.status_code == 400
        assert "follow yourself" in response.data["detail"].lower()

        # Unfollow
        url = reverse("unfollow-user", kwargs={"target_username": "jane_doe"})
        response = self.user_client.post(url)
        assert response.status_code == 200
        assert profile_2 not in profile_1.followed_users.all()

        # Try to unfollow again — should fail
        response = self.user_client.post(url)
        assert response.status_code == 400
        assert "not following" in response.data["detail"].lower()

class ReviewEndpointTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.isbn = "9783161484100"
        self.valid_review_data = {
            "rating": 5,
            "review": "This is a test review."
        }

    def test_create_review(self):
        url = reverse("create-review", kwargs={"isbn": self.isbn})
        response = self.user_client.post(url, self.valid_review_data)
        assert response.status_code == 201
        assert Review.objects.filter(user_profile=self.example_user_profile, book=self.example_book).exists()

    def test_create_review_twice_should_fail(self):
        Review.objects.create(user_profile=self.example_user_profile, book=self.example_book, **self.valid_review_data)
        url = reverse("create-review", kwargs={"isbn": self.isbn})
        response = self.user_client.post(url, self.valid_review_data)
        assert response.status_code == 400
        assert "already exists" in response.data["error"]

    def test_create_review_with_invalid_rating(self):
        url = reverse("create-review", kwargs={"isbn": self.isbn})
        response = self.user_client.post(url, {"rating": 999, "review": "invalid"})
        assert response.status_code == 400

    def test_edit_review(self):
        Review.objects.create(user_profile=self.example_user_profile, book=self.example_book, **self.valid_review_data)
        url = reverse("edit-review", kwargs={"isbn": self.isbn})
        updated_data = {"review": "Updated content", "rating": 4}
        response = self.user_client.post(url, updated_data)
        assert response.status_code == 200
        updated_review = Review.objects.get(user_profile=self.example_user_profile, book=self.example_book)
        assert updated_review.review == "Updated content"
        assert updated_review.rating == 4

    def test_edit_review_that_does_not_exist(self):
        url = reverse("edit-review", kwargs={"isbn": self.isbn})
        response = self.user_client.post(url, {"review": "nope", "rating": 3})
        assert response.status_code == 404
        assert "doesn't exist" in response.data["error"]

    def test_get_reviews_by_isbn(self):
        Review.objects.create(user_profile=self.example_user_profile, book=self.example_book, **self.valid_review_data)
        url = reverse("get-reviews-by-isbn", kwargs={"isbn": self.isbn})
        response = self.user_client.get(url)
        assert response.status_code == 200
        assert "reviews" in response.data
        assert len(response.data["reviews"]) == 1
        assert response.data["reviews"][0]["review"] == self.valid_review_data["review"]
        assert response.data["reviews"][0]["isbn13"] == self.isbn

    def test_get_reviews_by_nonexistent_isbn(self):
        url = reverse("get-reviews-by-isbn", kwargs={"isbn": "9999999999999"})
        response = self.user_client.get(url)
        assert response.status_code in [200, 404]

    def test_get_reviews_by_user(self):
        Review.objects.create(user_profile=self.example_user_profile, book=self.example_book, **self.valid_review_data)
        url = reverse("get-users-reviews")
        response = self.user_client.get(url)
        assert response.status_code == 200
        assert "reviews" in response.data
        assert len(response.data["reviews"]) == 1
        assert response.data["reviews"][0]["review"] == self.valid_review_data["review"]
        assert response.data["reviews"][0]["isbn13"] == self.isbn

    def test_get_reviews_by_user_with_no_reviews(self):
        new_user = User.objects.create_user(username="nouser", password="pass123")
        UserProfile.objects.create(user=new_user)
        client = Client()
        client.login(username="nouser", password="pass123")
        url = reverse("get-users-reviews")
        response = client.get(url)
        assert response.status_code == 200
        assert "reviews" in response.data
        assert len(response.data["reviews"]) == 0
