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
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_create_account(client):
    """Test account creation functionality."""
    response = client.post('/create-account', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code == 201
    assert json.loads(response.data)['message'] == 'Account created successfully'

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