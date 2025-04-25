from django.urls import reverse
import os
import requests
from main.models import Book
from main.views import add_book_to_db

def addBooksByLetter():
    alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']


    for letter in alphabet:
        rel_url = reverse("ext-books-by-title", kwargs={"title" : letter})
        abs_url = f'http://127.0.0.1:8000/{rel_url}'
        ext_response = requests.get(abs_url)
        ext_response_data = ext_response.json()
        #create book with first item
        print("checkings letter: " + letter)
        for serialized_book in ext_response_data["books_returned"]:
            add_book_to_db(serialized_book)
