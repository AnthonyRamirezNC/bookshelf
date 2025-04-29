
from openai import OpenAI
from main.models import Book
from main.serializers import BookSerializer
import time

#this script was used to normalize the 
# genres in the book dataset to help 
# with the recomender system AND IS DEPRECATED AND NOT TO BE USED
# WARNING THIS TOOL IS EXPENSIVE TO USE $3 PER USE AND PARSE


def normalizeGenres():
    client = OpenAI()
    system_prompt = """You are an esteemed research assistant whose passion project is properly categorizing books that have unclear, missing, or incorrect genres.
    Your task:

    - Read each book's Title, ID, ISBN, and existing (often bad) Genres.
    - Based on the Title and/or Genres, assign better, normalized genres.
    - You may assign multiple genres if appropriate (maximum 3), separated by a single space.
    - If the original genre is good, you can keep it; otherwise, correct or improve it.
    - If a book is missing a genre, DO NOT just pick a default value — carefully infer an appropriate genre based on the title and your expert knowledge.

    Accepted Genres (Choose only from this list; do not combine genres with slashes or create new genres):

    Fiction, Classics, Science Fiction, Fantasy, Mystery, Romance, Horror, Biography, Memoir, History, Poetry, Non-Fiction, Thriller, Suspense, Young Adult, Children's Literature, Adventure, Dystopian, Historical Fiction, Self-Help, Graphic Novels, Comics, Religion, Spirituality, True Crime, Humor, Comedy, Essays, Short Stories, Contemporary Fiction, Paranormal, Supernatural, LGBTQ+ Fiction, Urban Fantasy, Literary Fiction, Political Sciences, Social Sciences, Science, Nature, Philosophy, Art, Photography, Cookbooks, Food Writing, Business, Economics, Health, Wellness, Travel, Parenting, Family, Sports, Outdoors, Anthology, War, Military, Westerns, Crafts, Hobbies, Education, Teaching

    Input Format:
    Title;id;isbn;genre1 genre2 genre3 etc

    Output Format (Must match exactly):
    Title;id;isbn;updatedgenre1 updatedgenre2 updatedgenre3
    (keep Title, ID, ISBN exactly the same, just replace the genres)

    Example Input:
    The Aztecs;dae732f5-2db7-49b2-900b-2ce7def8d6e5;9780195379389;History
    Catherine the Great;ff56768d-b5cc-4030-9c83-9e4038b4151a;9780679456728;Biography & Autobiography
    AMER CYCLOPAEDIA;0d042f52-37f9-43af-8ec0-0d07562b279a;9781360209920;History
    The Encyclopaedia Britannica;7bb061b5-bfe7-4fea-ba20-8b2d8745fe5d;9781343790711;

    Example Output:
    The Aztecs;dae732f5-2db7-49b2-900b-2ce7def8d6e5;9780195379389;History
    Catherine the Great;ff56768d-b5cc-4030-9c83-9e4038b4151a;9780679456728;Biography History
    AMER CYCLOPAEDIA;0d042f52-37f9-43af-8ec0-0d07562b279a;9781360209920;History
    The Encyclopaedia Britannica;7bb061b5-bfe7-4fea-ba20-8b2d8745fe5d;9781343790711;History Non-Fiction
    """


    user_prompt = ""

    print("Serializing Books from DB")
    with open("bookData.txt", "a", encoding="utf-8") as f:
        #get all books
        books = Book.objects.all()
        for book in books:
            book_data_line = ""
            serialized_book = BookSerializer(book)
            serialized_book_data = serialized_book.data
            #add title    
            book_data_line += serialized_book_data["title"] + ";"
            #add id    
            book_data_line += serialized_book_data["id"] + ";"
            #add isbn    
            book_data_line += serialized_book_data["isbn13"] + ";"

            #add genres
            for genre in serialized_book_data["genres"]:
                book_data_line += genre + " "

            book_data_line += "\n"
            f.write(book_data_line)

    print("Chunking and sending to openAI")
    #now read file and send to openAI 100 books at a time
    with open("normalizedBookData.txt", "w", encoding="utf-8") as output_file:
        with open("bookData.txt", "r", encoding="utf-8") as f:
            count = 0
            for line in f.readlines():
                if(count < 100):
                    #add this line to prompt
                    user_prompt += line
                    count +=1
                else:
                    #done 100
                    # add this line to prompt or it will be ignored
                    user_prompt += line
                    #parse to open AI then reset count
                    response = client.chat.completions.create(
                        model="gpt-4",
                        temperature=0.0,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                    )

                    output_file.write(response.choices[0].message.content + "\n")
                    output_file.flush()

                    print("batch of 100 processed and finished")

                    user_prompt = ""
                    count = 0
                    time.sleep(2)

            if user_prompt.strip():
                response = client.chat.completions.create(
                    model="gpt-4",
                    temperature=0.0,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                output_file.write(response.choices[0].message.content + "\n")
                output_file.flush()

    print("Book genres corrected and written to normalizedBooksData.txt")

    #read from normalizedBookData and set each book in dataset to new genres
    with open("normalizedBookData.txt", "r", encoding="utf-8") as f:
        for count, line in enumerate(f.readlines()):
            lineArray = line.strip().split(";")
            if len(lineArray) >= 4:
                book_id = lineArray[1].strip()
                genre_field = lineArray[3].strip()

                # Simple clean split on space
                genres = genre_field.split(" ") if genre_field else []

                try:
                    book = Book.objects.get(id=book_id)
                    book.genres = genres  # assuming genres is a list field
                    book.save()

                    if count % 50 == 0:
                        print(f"Updated 50 books at count {count}")
                except Book.DoesNotExist:
                    print(f"Book with ID {book_id} not found. Count is: {count}")