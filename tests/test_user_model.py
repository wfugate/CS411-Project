import pytest
from flask import Flask
from movie_collection.db import db
from movie_collection.models.user_model import Users
import json

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    
    # Import and register your routes
    from movie_collection.app import create_account, login, update_password
    
    # Register the routes
    app.add_url_rule('/create-account', 'create_account', create_account, methods=['POST'])
    app.add_url_rule('/login', 'login', login, methods=['POST'])
    app.add_url_rule('/update-password', 'update_password', update_password, methods=['POST'])
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all() # Creates a fresh test database
        yield app
        db.drop_all() # Cleans up after tests

@pytest.fixture
def client(app):
    return app.test_client()

"""
    200: Success/OK (used for successful GET, PUT, or DELETE operations)
    201: Created (used when successfully creating a new resource, like in /create-account)
    400: Bad Request (when client sends invalid data)
    401: Unauthorized (when credentials are invalid)
    404: Not Found (when requested resource doesn't exist)
"""

def test_create_account(client):
    """Test account creation functionality."""
    response = client.post('/create-account', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code == 201
    assert json.loads(response.data)['message'] == 'Account created successfully'

def test_create_account_duplicate_username(client):
    """Test creating account with existing username."""
    # Create first user
    client.post('/create-account', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    
    # Try to create second user with same username
    response = client.post('/create-account', json={
        'username': 'testuser',
        'password': 'different_password'
    })
    assert response.status_code == 400
    assert "already exists" in json.loads(response.data)['error']

def test_login_success(client):
    """Test successful login."""
    # Create test user
    client.post('/create-account', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    
    # Test login
    response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code == 200
    assert json.loads(response.data)['message'] == 'Login successful'

def test_login_user_not_found(client):
    """Test login with non-existent username."""
    response = client.post('/login', json={
        'username': 'nonexistent',
        'password': 'testpass'
    })
    assert response.status_code == 404
    assert "not found" in json.loads(response.data)['error']

def test_login_invalid_password(client):
    """Test login with incorrect password."""
    # Create user
    client.post('/create-account', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    
    # Try login with wrong password
    response = client.post('/login', json={
        'username': 'testuser',
        'password': 'wrongpass'
    })
    assert response.status_code == 401
    assert "Invalid credentials" in json.loads(response.data)['error']

def test_update_password(client):
    """Test password update functionality."""
    # Create test user
    client.post('/create-account', json={
        'username': 'testuser',
        'password': 'oldpass'
    })
    
    # Update password
    response = client.post('/update-password', json={
        'username': 'testuser',
        'old_password': 'oldpass',
        'new_password': 'newpass'
    })
    assert response.status_code == 200
    assert json.loads(response.data)['message'] == 'Password updated successfully'

def test_update_password_user_not_found(client):
    """Test updating password for non-existent user."""
    response = client.post('/update-password', json={
        'username': 'nonexistent',
        'old_password': 'oldpass',
        'new_password': 'newpass'
    })
    assert response.status_code == 404
    assert "not found" in json.loads(response.data)['error']

def test_update_password_invalid_old_password(client):
    """Test updating password with incorrect old password."""
    # Create user
    client.post('/create-account', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    
    # Try updating with wrong old password
    response = client.post('/update-password', json={
        'username': 'testuser',
        'old_password': 'wrongpass',
        'new_password': 'newpass'
    })
    assert response.status_code == 401
    assert "Invalid" in json.loads(response.data)['error']