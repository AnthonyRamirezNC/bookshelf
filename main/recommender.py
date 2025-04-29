from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import pandas as pd
from .models import *


def build_recommendations(user):
    #get all book objects from the DB and convert to df 
    books = Book.objects.all()
    df = pd.DataFrame(list(books.values('id', 'title', 'authors', 'genres', 'description')))

    #get top 30 most common genres
    all_genres = [g for genre_list in df['genres'] for g in (genre_list or [])]
    genre_counts = Counter(all_genres)
    top_n = 30 
    top_genres = set(g for g, _ in genre_counts.most_common(top_n))

    #filter top genres 
    def filter_top_genres(genres):
        return [g for g in (genres or []) if g in top_genres]

    df['filtered_genres'] = df['genres'].apply(filter_top_genres)

    #build metadata string for vectorization
    df['metadata'] = df.apply(
        lambda row: ' '.join(row['filtered_genres']) + ' ' +
                    ' '.join(row['authors'] or []) + ' ' +
                    (row['description'] or ''),
        axis=1
    )

    #vectorizze metadata
    tfidf = TfidfVectorizer(stop_words='english', max_features=1000)
    tfidf_matrix = tfidf.fit_transform(df['metadata'])

    #get all of a users liked books
    liked_books = UserProfile.objects.get(user=user).liked_books 
    if not liked_books:
        return []
    liked_books = liked_books.values_list('id', flat=True)

    
    #Finds which rows in df match the liked book IDs
    liked_indices = df[df['id'].isin(liked_books)].index

    #compuute cos similarity
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    scores = cosine_sim[liked_indices].mean(axis=0)

    #add sim scores to df
    df['score'] = scores

     #get results without already liked books
    recommendations = df[~df['id'].isin(liked_books)].sort_values('score', ascending=False)
    
    # change value to recommend more or less books
    return list(recommendations.head(10)['id'])
