from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from .models import Book, BookInteraction


def build_recommendations(user):
    books = Book.objects.all()
    df = pd.vDataFrame(list(books.values('id', 'title', 'authors', 'genres')))

    df['metadata'] = df.apply(lambda row: ' '.join(row['genres'] or []) + ' ' + ' '.join(row['authors'] or []), axis=1)
    
    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(df['metadata'])

    liked_books = BookInteraction.objects.filter(user=user, liked=True).values_list('book_id', flat=True)

    if not liked_books:
        return []
    
    liked_indices = df[df['id'].isin(liked_books)].index

    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    scores = cosine_sim[liked_indices].mean(axis=0)

    df['score'] = scores
    recommendations = df[~df['id'].isin(liked_books)].sort_values('score', ascending=False)


    # change value to recommend more or less books
    return list(recommendations.head(5)['id'])
