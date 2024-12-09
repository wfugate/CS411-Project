from contextlib import contextmanager
import re
import sqlite3
import pytest

from movie_collection.models.movie_model import (
    Movie,
    create_movie,
    find_movie_by_name,
    find_movie_by_year,
    search_movie_by_language,
    search_movie_by_director,
    search_movie_by_genre,
)

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("movie_collection.models.movie_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

##########################################################
# Movie Creation Tests
##########################################################

def test_create_movie(mock_cursor):
    """Test creating a new movie in the catalog."""
    create_movie(
        name="Movie Title",
        year=2022,
        director="Director Name",
        genres=["Drama", "Action"],
        original_language="en",
    )

    expected_query = normalize_whitespace("""
        INSERT INTO movies (name, year, director, genres, original_language)
        VALUES (?, ?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ("Movie Title", 2022, "Director Name", "Drama, Action", "en")
    assert actual_arguments == expected_arguments, f"Arguments mismatch: expected {expected_arguments}, got {actual_arguments}."


def test_create_movie_duplicate(mock_cursor):
    """Test creating a movie with a duplicate name."""
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: movies.name")
    with pytest.raises(ValueError, match="Movie with name 'Movie Title' already exists"):
        create_movie(name="Movie Title", year=2022, director="Director Name", genres=["Drama", "Action"], original_language="en")


def test_create_movie_invalid_year():
    """Test error when creating a movie with invalid year."""
    with pytest.raises(ValueError, match="Invalid release year: 1887. Must be a valid integer year."):
        create_movie(name="Movie Title", year=1887, director="Director Name", genres=["Drama"], original_language="en")

    with pytest.raises(ValueError, match="Invalid release year: invalid. Must be a valid integer year."):
        create_movie(name="Movie Title", year="invalid", director="Director Name", genres=["Drama"], original_language="en")


def test_create_movie_invalid_genres():
    """Test error when creating a movie with invalid genres."""
    with pytest.raises(ValueError, match="Genres list cannot be empty."):
        create_movie(name="Movie Title", year=2022, director="Director Name", genres=[], original_language="en")

    with pytest.raises(ValueError, match="Genres list cannot be empty."):
        create_movie(name="Movie Title", year=2022, director="Director Name", genres=None, original_language="en")


def test_create_movie_invalid_language():
    """Test error when creating a movie with invalid original language."""
    with pytest.raises(ValueError, match="Invalid original language: ''. Must be a non-empty string."):
        create_movie(name = "Movie Title", year = 2022, director = "Director Name", genres = ["Drama"], original_language = "")

    with pytest.raises(ValueError, match="Invalid original language: '123'. Must be a non-empty string."):
        create_movie(name = "Movie Title", year = 2022, director = "Director Name", genres = ["Drama"], original_language = 123)

#    with pytest.raises(ValueError, match="Invalid original language: 123. Must be a non-empty string."):

##########################################################
# Movie Search Tests
##########################################################

def test_movie_invalid_year():
    """Test creating a Movie with invalid year."""
    with pytest.raises(ValueError, match="Year must be greater than 1900, got 1800"):
        Movie(
            name="Test Movie",
            year=1800,
            director="Test Director",
            genres=["Action"],
            original_language="en"
        )

def test_find_movie_by_name(mocker):
    """Test searching for a movie by name."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'results': [{
            'title': 'Test Movie',
            'release_date': '2023-01-01',
            'original_language': 'en',
            'genres': ['Test']
        }]
    }
    mocker.patch('requests.get', return_value=mock_response)
    
    movie = find_movie_by_name("Test Movie")
    assert movie.name == "Test Movie"
    assert movie.year == 2023
    assert movie.original_language == "en"

def test_find_movie_by_name_not_found(mocker):
    """Test searching for a non-existent movie."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {'results': []}
    mocker.patch('requests.get', return_value=mock_response)
    
    with pytest.raises(ValueError, match="No movies found."):
        find_movie_by_name("Nonexistent Movie")

def test_find_movie_by_year(mocker):
    """Test searching for a movie by year."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'results': [{
            'title': 'Test Movie',
            'release_date': '2023-01-01',
            'original_language': 'en',
            'genres': ["Test"]
        }]
    }
    mocker.patch('requests.get', return_value=mock_response)
    
    movie = find_movie_by_year(2023)
    assert movie.year == 2023
    assert isinstance(movie, Movie)

def test_find_movie_by_name_empty_input():
    """Test searching for a movie with empty name."""
    with pytest.raises(ValueError, match="No movies found."):
        find_movie_by_name("")

def test_find_movie_by_year_not_found(mocker):
    """Test searching for a movie in a year with no results."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {'results': []}
    mocker.patch('requests.get', return_value=mock_response)
    
    with pytest.raises(ValueError, match="No movies found for the year: '1800'."):
        find_movie_by_year(1800)

def test_find_movie_by_year_invalid_type():
    """Test searching for a movie with invalid year type."""
    with pytest.raises(ValueError, match="Year must be an integer"):
        find_movie_by_year("2023")

def test_find_movie_by_year_invalid_value():
    """Test searching for a movie with invalid year value."""
    with pytest.raises(ValueError, match="No movies found for the year: '1800'."):
        find_movie_by_year(1800)

def test_search_movie_by_language(mocker):
    """Test searching for a movie by language."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'results': [{
            'title': 'Test Movie',
            'release_date': '2023-01-01',
            'original_language': 'fr',
            'genres': ["Test"]
        }]
    }
    mocker.patch('requests.get', return_value=mock_response)
    
    movie = search_movie_by_language("fr")
    
    # Access the first result from the 'results' list
    result = mock_response.json()['results'][0]
    
    assert movie.original_language == result['original_language']
    assert isinstance(movie, Movie)

def test_search_movie_by_language_empty_input():
    """Test searching for a movie with empty language code."""
    with pytest.raises(ValueError, match="Language code cannot be empty"):
        search_movie_by_language("")

def test_search_movie_by_director(mocker):
    """Test searching for a movie by director."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'results': [{
            'id': 1,
            'name': 'Test Director'
        }]
    }
    mock_credits = mocker.Mock()
    mock_credits.json.return_value = {
        'crew': [{
            'job': 'Director',
            'title': 'Test Movie',
            'release_date': '2023-01-01',
            'original_language': 'en'
        }]
    }
    mocker.patch('requests.get', side_effect=[mock_response, mock_credits])
    
    movie = search_movie_by_director("Test Director")
    assert movie.director == "Test Director"
    assert isinstance(movie, Movie)

def test_search_movie_by_director_empty_input():
    """Test searching for a movie with empty director name."""
    with pytest.raises(ValueError, match="Director not found."):
        search_movie_by_director("")

def test_search_movie_by_director_not_found(mocker):
    """Test searching for a non-existent director."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {'results': []}
    mocker.patch('requests.get', return_value=mock_response)
    
    with pytest.raises(ValueError, match="Director not found."):
        search_movie_by_director("Nonexistent Director")

def test_search_movie_by_director_no_movies(mocker):
    """Test searching for a director with no movies."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'results': [{
            'id': 1,
            'name': 'Test Director'
        }]
    }
    mock_credits = mocker.Mock()
    mock_credits.json.return_value = {'crew': []}
    mocker.patch('requests.get', side_effect=[mock_response, mock_credits])
    
    with pytest.raises(ValueError, match="No movies found with the director 'Test Director'."):
        search_movie_by_director("Test Director")

def test_search_movie_by_genre(mocker):
    """Test searching for a movie by genre ID."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'results': [{
            'title': 'Test Movie',
            'release_date': '2023-01-01',
            'original_language': 'en',
            'genres': ['Test']
        }]
    }
    mocker.patch('requests.get', return_value=mock_response)
    
    movie = search_movie_by_genre(28)  # Action genre ID
    assert isinstance(movie, Movie)

def test_search_movie_by_genre_invalid_id():
    """Test searching for a movie with invalid genre ID."""
    with pytest.raises(ValueError, match="No movies found with the genre with ID '-1'"):
        search_movie_by_genre(-1)
