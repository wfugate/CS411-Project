from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from movie_collection.db import db
from movie_collection.models.user_model import Users
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

##########################################################
#
# Health Check
#
##########################################################

@app.route('/health', methods=['GET'])
def healthcheck():
    """
    Health check route to verify the service is running.

    Returns:
        JSON Response: {"status": "healthy"}, 200
    """
    logger.info('Health check requested')
    return make_response(jsonify({'status': 'healthy'}), 200)

##########################################################
#
# User Management
#
##########################################################

@app.route('/create-account', methods=['POST'])
def create_account():
    """
    Create a new user account with secure password storage.

    Expected JSON Input:
        - username (str): The username for the new user
        - password (str): The password to be hashed and stored

    Returns:
        JSON Response:
            - success: {"message": "Account created successfully"}, 201
            - error: {"error": error_message}, status_code

    Raises:
        400: If input validation fails
        500: If there is an issue adding the user to the database
    """
    logger.info('Creating new account')
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        logger.error('Missing username or password in request')
        return make_response(jsonify({'error': 'Invalid input, both username and password are required'}), 400)
    
    try:
        Users.create_user(username, password)
        logger.info('Account created successfully for user: %s', username)
        return make_response(jsonify({'message': 'Account created successfully'}), 201)
    except ValueError as e:
        logger.error('Value error during account creation: %s', str(e))
        return make_response(jsonify({'error': str(e)}), 400)
    except Exception as e:
        logger.error('Unexpected error during account creation: %s', str(e))
        return make_response(jsonify({'error': 'An error occurred while creating the account'}), 500)

@app.route('/login', methods=['POST'])
def login():
    """
    Verify user credentials against stored password hash.

    Expected JSON Input:
        - username (str): The username of the user
        - password (str): The password to verify

    Returns:
        JSON Response:
            - success: {"message": "Login successful"}, 200
            - error: {"error": error_message}, status_code

    Raises:
        400: If input validation fails
        401: If authentication fails
        404: If user not found
    """
    logger.info('Processing login request')
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        logger.error('Missing username or password in login request')
        return make_response(jsonify({'error': 'Invalid input, both username and password are required'}), 400)
    
    try:
        if Users.check_password(username, password):
            logger.info('Login successful for user: %s', username)
            return make_response(jsonify({'message': 'Login successful'}), 200)
        logger.warning('Failed login attempt for user: %s', username)
        return make_response(jsonify({'error': 'Invalid credentials'}), 401)
    except ValueError as e:
        logger.error('Value error during login: %s', str(e))
        return make_response(jsonify({'error': str(e)}), 404)
    except Exception as e:
        logger.error('Unexpected error during login: %s', str(e))
        return make_response(jsonify({'error': 'An error occurred during login'}), 500)

@app.route('/update-password', methods=['POST'])
def update_password():
    """
    Update a user's password after verifying their current password.

    Expected JSON Input:
        - username (str): The username of the user
        - old_password (str): The current password
        - new_password (str): The new password to set

    Returns:
        JSON Response:
            - success: {"message": "Password updated successfully"}, 200
            - error: {"error": error_message}, status_code

    Raises:
        400: If input validation fails
        401: If old password is invalid
        404: If user not found
    """
    logger.info('Processing password update request')
    data = request.get_json()
    username = data.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not username or not old_password or not new_password:
        logger.error('Missing required fields in password update request')
        return make_response(jsonify({'error': 'Username, old password, and new password are required'}), 400)
    
    try:
        if Users.check_password(username, old_password):
            Users.update_password(username, new_password)
            logger.info('Password updated successfully for user: %s', username)
            return make_response(jsonify({'message': 'Password updated successfully'}), 200)
        logger.warning('Invalid old password provided for user: %s', username)
        return make_response(jsonify({'error': 'Invalid old password'}), 401)
    except ValueError as e:
        logger.error('Value error during password update: %s', str(e))
        return make_response(jsonify({'error': str(e)}), 404)
    except Exception as e:
        logger.error('Unexpected error during password update: %s', str(e))
        return make_response(jsonify({'error': 'An error occurred while updating the password'}), 500)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        logger.info('Database tables created successfully')
    app.run(debug=True)