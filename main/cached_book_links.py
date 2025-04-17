# myapp/cached_data.py

import pandas as pd

df = None  # global reference

def load_df():
    global df
    df = pd.read_csv('Books.csv')

def get_link_with_ISBN(isbn):
    match = df[df['ISBN'] == isbn]
    if not match.empty:
        return match.iloc[0]['Image-URL-M']
    return None