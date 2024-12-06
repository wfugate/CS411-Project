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
    """
    A class representing a movie with basic information.

    Attributes:
        name (str): The title of the movie
        year (int): The release year of the movie
        director (str): The director of the movie
        genres (list): List of genres associated with the movie
        original_language (str): The original language of the movie
    """
    name: str
    year: int
    director: str
    genres: list
    original_language: str

    def __post_init__(self):
        if self.year <= 1900:
            raise ValueError(f"Year must be greater than 1900, got {self.year}")


def find_movie_by_name(name: str) -> Movie:
    """
    Search for a movie by its name using the TMDB API.

    Args:
        name (str): The name of the movie to search for.

    Returns:
        Movie: A Movie object containing the movie information.

    Raises:
        ValueError: If no movies are found with the given name.
    """
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
    """
    Search for a random movie from a specific year using the TMDB API.

    Args:
        year (int): The year to search for movies.

    Returns:
        Movie: A Movie object containing the movie information.

    Raises:
        ValueError: If no movies are found for the given year or if the year is invalid.
    """
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
    """
    Search for movies by original language using the TMDB API.

    Args:
        language_code (str): The language code to search for.

    Returns:
        Movie: A Movie object containing the movie information.

    Raises:
        ValueError: If no movies are found for the given language or if the language code is invalid.
    """
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
    """
    Search for movies by a specific director using the TMDB API.

    Args:
        director_name (str): The name of the director to search for.

    Returns:
        Movie: A Movie object containing the movie information.

    Raises:
        ValueError: If the director is not found or if no movies are found for the director.
    """
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
    """
    Search for movies by genre using the TMDB API.

    Args:
        genre_id (int): The ID of the genre to search for.

    Returns:
        Movie: A Movie object containing the movie information.

    Raises:
        ValueError: If no movies are found for the given genre or if the genre ID is invalid.
    """
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

