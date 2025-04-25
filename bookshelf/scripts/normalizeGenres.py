
from openai import OpenAI
from main.models import Book
from main.serializers import BookSerializer
def normalizeGenres():
    client = OpenAI()

    with open("bookData.txt", "a") as f:
        #get all books
        books = Book.objects.all()
        for book in books:
            book_data_line = ""
            serialized_book = BookSerializer(book)
            #add title    
            book_data_line += serialized_book.title + " "
            #add id    
            book_data_line += serialized_book.id + " "
            #add isbn    
            book_data_line += serialized_book.isbn13 + " "

            #add genres
            for genre in serialized_book.genres:
                book_data_line += genre + " "

            book_data_line += "\n"
            f.write(book_data_line)


