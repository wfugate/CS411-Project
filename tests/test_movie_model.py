import pytest
from movie_collection.models.movie_model import Movie, find_movie_by_name, find_movie_by_year, search_movie_by_language, search_movie_by_director, search_movie_by_genre

@pytest.fixture
def sample_movie():
    return Movie(
        name="Test Movie",
        year=2023,
        director="Test Director",
        genres=["Action", "Drama"],
        original_language="en"
    )

##########################################################
# Movie Search Tests
##########################################################

def test_find_movie_by_name(mocker):
    """Test searching for a movie by name."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'results': [{
            'title': 'Test Movie',
            'release_date': '2023-01-01',
            'original_language': 'en',
            'genres': []
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
            'genres': []
        }]
    }
    mocker.patch('requests.get', return_value=mock_response)
    
    movie = find_movie_by_year(2023)
    assert movie.year == 2023
    assert isinstance(movie, Movie)

def test_find_movie_by_year_not_found(mocker):
    """Test searching for a movie in a year with no results."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {'results': []}
    mocker.patch('requests.get', return_value=mock_response)
    
    with pytest.raises(ValueError, match="No movies found for this year."):
        find_movie_by_year(1800)

def test_search_movie_by_language(mocker):
    """Test searching for a movie by language."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'results': [{
            'title': 'Test Movie',
            'release_date': '2023-01-01',
            'original_language': 'fr',
            'genres': []
        }]
    }
    mocker.patch('requests.get', return_value=mock_response)
    
    movie = search_movie_by_language("fr")
    assert movie.original_language == "fr"
    assert isinstance(movie, Movie)

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

def test_search_movie_by_genre(mocker):
    """Test searching for a movie by genre ID."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'results': [{
            'title': 'Test Movie',
            'release_date': '2023-01-01',
            'original_language': 'en',
            'genres': []
        }]
    }
    mocker.patch('requests.get', return_value=mock_response)
    
    movie = search_movie_by_genre(28)  # Action genre ID
    assert isinstance(movie, Movie)