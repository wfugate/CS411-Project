from dataclasses import dataclass
import logging
import os
import sqlite3

from movie_collection.utils.logger import configure_logger
import requests
import random

logger = logging.getLogger(__name__)
configure_logger(logger)



@dataclass
class Movie:
    name: str
    year: int
    director: str
    genres: list
    original_language: str


    def __post_init__(self):
        if self.duration <= 0:
            raise ValueError(f"Duration must be greater than 0, got {self.duration}")
        if self.year <= 1900:
            raise ValueError(f"Year must be greater than 1900, got {self.year}")


def find_movie_by_name(name: str) -> Movie:
    """Search for a movie by its name and return a Movie object."""
    url = f"{BASE_URL}/search/movie"
    params = {'api_key': API_KEY, 'query': name}
    
    response = requests.get(url, params=params)
    data = response.json()

    if 'results' in data and data['results']:
        random_movie = random.choice(data['results'])
        movie_name = random_movie['title']
        release_year = int(random_movie['release_date'][:4])
        original_language = random_movie['original_language']
        
        # Get the director
        director = "Unknown"
        for crew_member in random_movie.get('credits', {}).get('crew', []):
            if crew_member['job'] == 'Director':
                director = crew_member['name']
                break
        
        # Get the genres
        genres = [genre['name'] for genre in random_movie.get('genres', [])]

        return Movie(
            name=movie_name,
            year=release_year,
            director=director,
            genres=genres,
            original_language=original_language
        )



    else:
        raise ValueError("No movies found.")

def find_movie_by_year(year: int) -> Movie:
    """Search for a random movie by year and return a Movie object."""
    url = f"{BASE_URL}/discover/movie"
    params = {'api_key': API_KEY, 'primary_release_year': year}
    
    response = requests.get(url, params=params)
    data = response.json()

    if 'results' in data and data['results']:
        random_movie = random.choice(data['results'])
        movie_name = random_movie['title']
        release_year = int(random_movie['release_date'][:4])
        original_language = random_movie['original_language']
        
        # Get the director
        director = "Unknown"
        for crew_member in random_movie.get('credits', {}).get('crew', []):
            if crew_member['job'] == 'Director':
                director = crew_member['name']
                break
        
        # Get the genres
        genres = [genre['name'] for genre in random_movie.get('genres', [])]

        return Movie(
            name=movie_name,
            year=release_year,
            director=director,
            genres=genres,
            original_language=original_language
        )
    else:
        raise ValueError("No movies found for this year.")
        
def search_movie_by_language(language_code: str) -> Movie:
    """Search for movies by original language and return a Movie object."""
    url = f"{BASE_URL}/discover/movie"
    params = {'api_key': API_KEY, 'language': language_code}
    
    response = requests.get(url, params=params)
    data = response.json()

    if 'results' in data and data['results']:
        random_movie = random.choice(data['results'])
        movie_name = random_movie['title']
        release_year = int(random_movie['release_date'][:4])
        original_language = random_movie['original_language']
        
        # Get the director
        director = "Unknown"
        for crew_member in random_movie.get('credits', {}).get('crew', []):
            if crew_member['job'] == 'Director':
                director = crew_member['name']
                break
        
        # Get the genres
        genres = [genre['name'] for genre in random_movie.get('genres', [])]

        return Movie(
            name=movie_name,
            year=release_year,
            director=director,
            genres=genres,
            original_language=original_language
        )
    else:
        raise ValueError("No movies found for this language.")
    
def search_movie_by_director(director_name: str) -> Movie:
    """Search for movies by a specific director and return a Movie object."""
    # Step 1: Search for the director's person ID
    url = f"{BASE_URL}/search/person"
    params = {'api_key': API_KEY, 'query': director_name}
    
    response = requests.get(url, params=params)
    data = response.json()

    if 'results' in data and data['results']:
        person_id = data['results'][0]['id']
        
        # Step 2: Get the director's movie credits
        url = f"{BASE_URL}/person/{person_id}/movie_credits"
        response = requests.get(url, params={'api_key': API_KEY})
        credits = response.json()
        
        # Filter movies directed by the person
        directed_movies = [movie for movie in credits['crew'] if movie['job'] == 'Director']
        
        if directed_movies:
            random_movie = random.choice(directed_movies)
            movie_name = random_movie['title']
            release_year = int(random_movie['release_date'][:4])
            original_language = random_movie['original_language']
            
            # Get the genres
            genres = [genre['name'] for genre in random_movie.get('genres', [])]

            return Movie(
                name=movie_name,
                year=release_year,
                director=director_name,
                genres=genres,
                original_language=original_language
            )
        else:
            raise ValueError("No directed movies found for this director.")
    else:
        raise ValueError("Director not found.")

def search_movie_by_genre(genre_id: int) -> Movie:
    """Search for movies by genre and return a Movie object."""
    url = f"{BASE_URL}/discover/movie"
    params = {'api_key': API_KEY, 'with_genres': genre_id}
    
    response = requests.get(url, params=params)
    data = response.json()

    if 'results' in data and data['results']:
        random_movie = random.choice(data['results'])
        movie_name = random_movie['title']
        release_year = int(random_movie['release_date'][:4])
        original_language = random_movie['original_language']
        
        # Get the director
        director = "Unknown"
        for crew_member in random_movie.get('credits', {}).get('crew', []):
            if crew_member['job'] == 'Director':
                director = crew_member['name']
                break
        
        # Get the genres
        genres = [genre['name'] for genre in random_movie.get('genres', [])]

        return Movie(
            name=movie_name,
            year=release_year,
            director=director,
            genres=genres,
            original_language=original_language
        )
    else:
        raise ValueError("No movies found for this genre.")

