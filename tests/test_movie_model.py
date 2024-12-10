from contextlib import contextmanager
import re
import sqlite3
import pytest

from movie_collection.models.movie_model import (
    Movie,
    add_movie_to_list,
    delete_movie_from_list, 
    clear_movie_list,
    find_movie_by_name,
    find_movie_by_year,
    find_movie_by_language,
    find_movie_by_director,
    find_movie_by_genre,
    mark_movie_as_favorite,
    list_favorite_movies
)

######################################################
#
#    Fixtures
#
######################################################

@pytest.fixture(scope="session", autouse=True)
def clear_table_before_suite():
    """Clear the movies table before running the test suite."""
    with sqlite3.connect('movies.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM movies")  # Clear all records in the table
        conn.commit()
    yield  # This ensures the tests are run after the table is cleared


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

def test_add_movie_to_list(mock_cursor):
    """Test creating a new movie in the catalog."""
    add_movie_to_list(
        name="Movie Title",
        year=2022,
        director="Director Name",
        genres=["Drama", "Action"],
        original_language="en",
    )

    expected_query = normalize_whitespace("""
        INSERT INTO movies (name, year, director, genres, original_language, favorite)
        VALUES (?, ?, ?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ("Movie Title", 2022, "Director Name", "Drama, Action", "en", False)
    assert actual_arguments == expected_arguments, f"Arguments mismatch: expected {expected_arguments}, got {actual_arguments}."


def test_create_movie_duplicate(mock_cursor):
    """Test creating a movie with a duplicate name."""
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: movies.name")
    with pytest.raises(ValueError, match="Movie with name 'Movie Title' already exists"):
        add_movie_to_list(name="Movie Title", year=2022, director="Director Name", genres=["Drama", "Action"], original_language="en")


def test_create_movie_invalid_year():
    """Test error when creating a movie with invalid year."""
    with pytest.raises(ValueError, match="Invalid release year: 1887. Must be a valid integer year."):
        add_movie_to_list(name="Movie Title", year=1887, director="Director Name", genres=["Drama"], original_language="en")

    with pytest.raises(ValueError, match="Invalid release year: invalid. Must be a valid integer year."):
        add_movie_to_list(name="Movie Title", year="invalid", director="Director Name", genres=["Drama"], original_language="en")


def test_create_movie_invalid_genres():
    """Test error when creating a movie with invalid genres."""
    with pytest.raises(ValueError, match="Genres list cannot be empty."):
        add_movie_to_list(name="Movie Title", year=2022, director="Director Name", genres=[], original_language="en")

    with pytest.raises(ValueError, match="Genres list cannot be empty."):
        add_movie_to_list(name="Movie Title", year=2022, director="Director Name", genres=None, original_language="en")


def test_create_movie_invalid_language():
    """Test error when creating a movie with invalid original language."""
    with pytest.raises(ValueError, match="Invalid original language: ''. Must be a non-empty string."):
        add_movie_to_list(name = "Movie Title", year = 2022, director = "Director Name", genres = ["Drama"], original_language = "")

    with pytest.raises(ValueError, match="Invalid original language: '123'. Must be a non-empty string."):
        add_movie_to_list(name = "Movie Title", year = 2022, director = "Director Name", genres = ["Drama"], original_language = 123)

def test_add_movie_with_favorite(mock_cursor):
    """Test creating a new movie with the favorite flag set to True."""
    add_movie_to_list(
        name="Favorite Movie",
        year=2023,
        director="Director",
        genres=["Action"],
        original_language="en",
        favorite=True
    )

    expected_query = normalize_whitespace("""
        INSERT INTO movies (name, year, director, genres, original_language, favorite)
        VALUES (?, ?, ?, ?, ?, ?)
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ("Favorite Movie", 2023, "Director", "Action", "en", True)
    assert actual_arguments == expected_arguments, f"Arguments mismatch: expected {expected_arguments}, got {actual_arguments}."

def test_add_movie_default_favorite(mock_cursor):
    """Test creating a new movie without specifying the favorite flag."""
    add_movie_to_list(
        name="Default Movie",
        year=2022,
        director="Director",
        genres=["Drama"],
        original_language="en"
    )

    expected_arguments = ("Default Movie", 2022, "Director", "Drama", "en", False)
    actual_arguments = mock_cursor.execute.call_args[0][1]
    assert actual_arguments == expected_arguments, f"Arguments mismatch: expected {expected_arguments}, got {actual_arguments}."



##########################################################
# Clear Catalog
##########################################################

def test_clear_movie_list(mock_cursor, mocker):
    """Test clearing the entire movie catalog (removes all movies)."""

    # Mock the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_movie_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))

    # Call the clear_database function
    clear_movie_list()

    # Ensure the file was opened using the environment variable's path
    mock_open.assert_called_once_with('sql/create_movie_table.sql', 'r')

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once()

##########################################################
# Movie Deletion Tests
##########################################################

def test_delete_movie(mock_cursor):
    """Test soft deleting a movie from the catalog by movie ID."""

    # Simulate that the movie exists (id = 1)
    mock_cursor.fetchone.return_value = ([False])

    # Call the delete_movie function
    delete_movie_from_list(1)

    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM movies WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE movies SET deleted = TRUE WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."


def test_delete_movie_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent movie."""

    # Simulate that no movie exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent movie
    with pytest.raises(ValueError, match="Movie with ID 999 not found"):
        delete_movie_from_list(999)

def test_delete_movie_already_deleted(mock_cursor):
    """Test error when trying to delete a movie that's already marked as deleted."""

    # Simulate that the movie exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a movie that's already been deleted
    with pytest.raises(ValueError, match="Movie with ID 999 has already been deleted"):
        delete_movie_from_list(999)

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
            'title': 'Test Movie 1',
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
            'title': 'Test Movie 2',
            'release_date': '2023-01-01',
            'original_language': 'fr',
            'genres': ["Test"]
        }]
    }
    mocker.patch('requests.get', return_value=mock_response)
    
    movie = find_movie_by_language("fr")
    
    # Access the first result from the 'results' list
    result = mock_response.json()['results'][0]
    
    assert movie.original_language == result['original_language']
    assert isinstance(movie, Movie)

def test_search_movie_by_language_empty_input():
    """Test searching for a movie with empty language code."""
    with pytest.raises(ValueError, match="Language code cannot be empty"):
        find_movie_by_language("")

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
            'title': 'Test Movie 3',
            'release_date': '2023-01-01',
            'original_language': 'en',
            'genres': '[Test]'
        }]
    }
    mocker.patch('requests.get', side_effect=[mock_response, mock_credits])
    
    movie = find_movie_by_director("Test Director")
    assert movie.director == "Test Director"
    assert isinstance(movie, Movie)

def test_search_movie_by_director_empty_input():
    """Test searching for a movie with empty director name."""
    with pytest.raises(ValueError, match="Director not found."):
        find_movie_by_director("")

def test_search_movie_by_director_not_found(mocker):
    """Test searching for a non-existent director."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {'results': []}
    mocker.patch('requests.get', return_value=mock_response)
    
    with pytest.raises(ValueError, match="Director not found."):
        find_movie_by_director("Nonexistent Director")

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
        find_movie_by_director("Test Director")

def test_search_movie_by_genre(mocker):
    """Test searching for a movie by genre ID."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'results': [{
            'title': 'Test Movie 4',
            'release_date': '2023-01-01',
            'original_language': 'en',
            'genres': ['Test']
        }]
    }
    mocker.patch('requests.get', return_value=mock_response)
    
    movie = find_movie_by_genre(28)  # Action genre ID
    assert isinstance(movie, Movie)

def test_search_movie_by_genre_invalid_id():
    """Test searching for a movie with invalid genre ID."""
    with pytest.raises(ValueError, match="No movies found with the genre with ID '-1'"):
        find_movie_by_genre(-1)

def test_mark_movie_as_favorite(mock_cursor):
    """Test marking a movie as favorite."""
    # Simulate the movie existing in the database
    mock_cursor.fetchone.return_value = (1,)  # Movie with ID 1 exists

    # Call the function
    mark_movie_as_favorite("Test Movie")

    # Verify the SELECT query to check for the movie
    expected_select_query = "SELECT id FROM movies WHERE name = ?"
    actual_select_query = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    assert actual_select_query == normalize_whitespace(expected_select_query)

    # Verify the UPDATE query to mark the movie as favorite
    expected_update_query = "UPDATE movies SET favorite = TRUE WHERE name = ?"
    actual_update_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])
    assert actual_update_query == normalize_whitespace(expected_update_query)

    # Verify the arguments for the queries
    assert mock_cursor.execute.call_args_list[0][0][1] == ("Test Movie",)  # SELECT args
    assert mock_cursor.execute.call_args_list[1][0][1] == ("Test Movie",)  # UPDATE args


def test_mark_movie_as_favorite_movie_not_found(mock_cursor):
    """Test marking a movie as favorite when the movie does not exist."""
    # Simulate the movie not existing in the database
    mock_cursor.fetchone.return_value = None  # No result for SELECT

    # Expect a ValueError
    with pytest.raises(ValueError, match="Movie with name 'Nonexistent Movie' not found."):
        mark_movie_as_favorite("Nonexistent Movie")

    # Verify the SELECT query was executed
    expected_query = "SELECT id FROM movies WHERE name = ?"
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == normalize_whitespace(expected_query)

def test_list_favorite_movies(mock_cursor):
    """Test retrieving all favorite movies."""
    # Simulate favorite movies in the database
    mock_cursor.fetchall.return_value = [("Test Movie 1",), ("Test Movie 2",)]

    # Call the function
    favorite_movies = list_favorite_movies()

    # Verify the SELECT query
    expected_query = "SELECT name FROM movies WHERE favorite = TRUE"
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == normalize_whitespace(expected_query)

    # Verify the result
    assert favorite_movies == ["Test Movie 1", "Test Movie 2"]


def test_list_favorite_movies_empty(mock_cursor):
    """Test retrieving favorite movies when no favorites exist."""
    # Simulate no favorite movies in the database
    mock_cursor.fetchall.return_value = []

    # Call the function
    favorite_movies = list_favorite_movies()

    # Verify the result
    assert favorite_movies == []

