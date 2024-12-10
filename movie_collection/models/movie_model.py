from dataclasses import dataclass
from contextlib import contextmanager
import logging
import os
import sqlite3

from movie_collection.utils.logger import configure_logger
import requests
import random

API_KEY = 'd3931fa0f5369b7ba2bb2981001bb8f9'
BASE_URL = 'https://api.themoviedb.org/3'

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('movies.db') 
    try:
        yield conn
    finally:
        conn.close()


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
        favorite (bool): favorite status of the movie
    """
    name: str
    year: int
    director: str
    genres: list
    original_language: str
    favorite: bool = False

    def __post_init__(self):
        if self.year <= 1900:
            raise ValueError(f"Year must be greater than 1900, got {self.year}")

def add_movie_to_list(name: str, year: int, director: str, genres: list, original_language: str, favorite: bool = False) -> None:
    """
    Add a movie to the database.

    Args:
        name (str): The name of the movie.
        year (int): The release year of the movie.
        director (str): The director of the movie.
        genres (list): A list of genres associated with the movie.
        original_language (str): The original language of the movie.
        favorite (bool, optional): Whether the movie is marked as a favorite. Defaults to False.

    Raises:
        ValueError: If the input data is invalid (e.g., empty genres list, invalid year).
        ValueError: If a movie with the given name already exists in the database.
        sqlite3.Error: If a database error occurs while adding the movie.
    """
    if not isinstance(year, int) or year < 1900:
        raise ValueError(f"Invalid release year: {year}. Must be a valid integer year greater than 1900.")
    if not genres:
        raise ValueError("Genres list cannot be empty.")
    if not isinstance(original_language, str) or not original_language:
        raise ValueError(f"Invalid original language: '{original_language}'. Must be a non-empty string.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO movies (name, year, director, genres, original_language, favorite)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, year, director, ', '.join(genres), original_language, favorite))
            conn.commit()
            logger.info("Movie successfully added to the database: %s", name)
    except sqlite3.IntegrityError:
        raise ValueError(f"Movie with name '{name}' already exists")
    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e


def delete_movie_from_list(movie_id: int) -> None:
    """
    Soft deletes a movie from the catalog by marking it as deleted.

    Args:
        movie_id (int): The ID of the movie to delete.

    Raises:
        ValueError: If the movie with the given ID does not exist or is already marked as deleted.
        sqlite3.Error: If any database error occurs.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if the movie exists and if it's already deleted
            cursor.execute("SELECT deleted FROM movies WHERE id = ?", (movie_id,))
            result = cursor.fetchone()

            if result is None:
                logger.info("Movie with ID %s not found", movie_id)
                raise ValueError(f"Movie with ID {movie_id} not found")

            deleted = result[0]
            if deleted:
                logger.info("Movie with ID %s has already been deleted", movie_id)
                raise ValueError(f"Movie with ID {movie_id} has already been deleted")

            # Perform the soft delete by setting 'deleted' to TRUE
            cursor.execute("UPDATE movies SET deleted = TRUE WHERE id = ?", (movie_id,))
            conn.commit()

            logger.info("Movie with ID %s marked as deleted.", movie_id)

    except sqlite3.Error as e:
        logger.error("Database error while deleting movie: %s", str(e))
        raise e

def clear_movie_list() -> None:
    """
    Recreates the movie table, effectively deleting all movies.

    Raises:
        sqlite3.Error: If any database error occurs.
    """
    try:
        with open(os.getenv("SQL_CREATE_TABLE_PATH", "/app/sql/create_movie_table.sql"), "r") as fh:
            create_table_script = fh.read()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(create_table_script)
            conn.commit()

            logger.info("Catalog cleared successfully.")

    except sqlite3.Error as e:
        logger.error("Database error while clearing catalog: %s", str(e))
        raise e
        

def find_movie_by_name(name: str) -> Movie:
    """
    Search for a movie by name using the TMDB API.

    Args:
        name (str): The name of the movie to search for.

    Returns:
        Movie: A Movie object containing the movie information, including favorite status.

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
        release_date = random_movie['release_date']
        release_year = int(release_date[:4])
        original_language = random_movie['original_language']
        genres = random_movie.get('genres', [])
        director = "Unknown"
        for crew_member in random_movie.get('credits', {}).get('crew', []):
            if crew_member['job'] == 'Director':
                director = crew_member['name']
                break

        add_movie_to_list(movie_name, release_year, director, genres, original_language)

        return Movie(
            name=movie_name,
            year=release_year,
            director=director, 
            genres=genres,
            original_language=original_language,
        )
    else:
        raise ValueError("No movies found.")
    

def mark_movie_as_favorite(name: str) -> None:
    """
    Marks a movie as a favorite in the database.

    Args:
        name (str): The name of the movie to mark as favorite.

    Raises:
        ValueError: If the movie with the given name does not exist in the database.
        sqlite3.Error: If any database error occurs.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if the movie exists
            cursor.execute("SELECT id FROM movies WHERE name = ?", (name,))
            result = cursor.fetchone()

            if result is None:
                raise ValueError(f"Movie with name '{name}' not found.")

            # Update the favorite status
            cursor.execute("UPDATE movies SET favorite = TRUE WHERE name = ?", (name,))
            conn.commit()

            logger.info("Movie '%s' marked as favorite.", name)

    except sqlite3.Error as e:
        logger.error("Database error while marking movie as favorite: %s", str(e))
        raise e
    
def list_favorite_movies() -> list:
    """
    Fetches the names of all favorite movies from the database.

    Returns:
        list: A list of movie names marked as favorite.

    Raises:
        sqlite3.Error: If any database error occurs.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM movies WHERE favorite = TRUE")
            results = cursor.fetchall()

            # Extract movie names from query results
            favorite_movies = [row[0] for row in results]

            logger.info("Favorite movies retrieved: %s", favorite_movies)
            return favorite_movies

    except sqlite3.Error as e:
        logger.error("Database error while retrieving favorite movies: %s", str(e))
        raise e


##############################################################
#
# find_movie functions
#
##############################################################

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

    if not isinstance(year, int):
        raise ValueError("Year must be an integer")

    if 'results' in data and data['results']:
        random_movie = random.choice(data['results'])
        movie_name = random_movie['title']
        release_date = random_movie['release_date']
        release_year = int(release_date[:4])
        original_language = random_movie['original_language']
        genres = random_movie.get('genres', [])
        director = "Unknown"
        for crew_member in random_movie.get('credits', {}).get('crew', []):
            if crew_member['job'] == 'Director':
                director = crew_member['name']
                break

        add_movie_to_list(movie_name, release_year, director, genres, original_language)
        return Movie(
            movie_name,
            release_year,
            director,
            genres,
            original_language
        )
    else:
        raise ValueError(f"No movies found for the year: '{year}'.")

def find_movie_by_language(language_code: str) -> Movie:
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

    if not language_code:
        raise ValueError("Language code cannot be empty")

    if 'results' in data and data['results']:
        random_movie = random.choice(data['results'])
        movie_name = random_movie['title']
        release_date = random_movie['release_date']
        release_year = int(release_date[:4])
        original_language = random_movie['original_language']
        genres = random_movie.get('genres', [])
        director = "Unknown"
        for crew_member in random_movie.get('credits', {}).get('crew', []):
            if crew_member['job'] == 'Director':
                director = crew_member['name']
                break

        add_movie_to_list(movie_name, release_year, director, genres, original_language)

        return Movie(
            movie_name,
            release_year,
            director,
            genres,
            original_language
        )
    else:
        raise ValueError(f"Invalid original language: '{original_language}'. Must be a non-empty string.")
    
def find_movie_by_director(director_name: str) -> Movie:
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

        url = f"{BASE_URL}/person/{person_id}/movie_credits"
        response = requests.get(url, params={'api_key': API_KEY})
        credits = response.json()

        directed_movies = [movie for movie in credits['crew'] if movie['job'] == 'Director']
        
        if directed_movies:
            random_movie = random.choice(directed_movies)
            movie_name = random_movie['title']
            release_date = random_movie['release_date']
            release_year = int(release_date[:4])
            original_language = random_movie['original_language']
            genres = random_movie.get('genres', [])

            add_movie_to_list(movie_name, release_year, director_name, genres, original_language)
            
            return Movie(
                movie_name,
                release_year,
                director_name,
                genres,
                original_language
            )
        else:
            raise ValueError(f"No movies found with the director '{director_name}'.")
    else: 
        raise ValueError(f"Director not found.")

def find_movie_by_genre(genre_id: int) -> Movie:
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
        release_date = random_movie['release_date']
        release_year = int(release_date[:4])
        original_language = random_movie['original_language']
        genres = random_movie.get('genres', [])
        director = "Unknown"
        for crew_member in random_movie.get('credits', {}).get('crew', []):
            if crew_member['job'] == 'Director':
                director = crew_member['name']
                break

        add_movie_to_list(movie_name, release_year, director, genres, original_language)

        return Movie(
            movie_name,
            release_year,
            director,
            genres,
            original_language,
        )
    else:
        raise ValueError(f"No movies found with the genre with ID '{genre_id}'.")

