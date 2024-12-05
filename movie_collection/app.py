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

@app.route('/health', methods=['GET'])
def healthcheck():
    """
    Health check route to verify the service is running.

    Returns:
        JSON response indicating the health status of the service.
    """
    logger.info('Health check requested')
    return make_response(jsonify({'status': 'healthy'}), 200)

@app.route('/create-account', methods=['POST'])
def create_account():
    """
    Create a new user account with secure password storage.

    Request JSON Parameters:
        username (str): The username for the new account
        password (str): The password to be hashed and stored

    Returns:
        JSON Response:
            - success: {"message": "Account created successfully"}, 201
            - error: {"error": error_message}, status_code
    """
    logger.info('Creating new account')
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        logger.error('Missing username or password in request')
        return make_response(jsonify({"error": "Username and password are required"}), 400)
    
    try:
        Users.create_user(username, password)
        logger.info(f"Account created successfully for user: {username}")
        return make_response(jsonify({"message": "Account created successfully"}), 201)
    except ValueError as e:
        logger.error(f"Value error during account creation: {str(e)}")
        return make_response(jsonify({"error": str(e)}), 400)
    except Exception as e:
        logger.error(f"Unexpected error during account creation: {str(e)}")
        return make_response(jsonify({"error": "An error occurred while creating the account"}), 500)

@app.route('/login', methods=['POST'])
def login():
    """
    Verify user credentials against stored password hash.

    Request JSON Parameters:
        username (str): The username of the user
        password (str): The password to verify

    Returns:
        JSON Response:
            - success: {"message": "Login successful"}, 200
            - error: {"error": error_message}, status_code
    """
    logger.info('Processing login request')
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        logger.error('Missing username or password in login request')
        return make_response(jsonify({"error": "Username and password are required"}), 400)
    
    try:
        if Users.check_password(username, password):
            logger.info(f"Successful login for user: {username}")
            return make_response(jsonify({"message": "Login successful"}), 200)
        logger.warning(f"Failed login attempt for user: {username}")
        return make_response(jsonify({"error": "Invalid credentials"}), 401)
    except ValueError as e:
        logger.error(f"Value error during login: {str(e)}")
        return make_response(jsonify({"error": str(e)}), 404)
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        return make_response(jsonify({"error": "An error occurred during login"}), 500)

@app.route('/update-password', methods=['POST'])
def update_password():
    """
    Update a user's password after verifying their current password.

    Request JSON Parameters:
        username (str): The username of the user
        old_password (str): The current password
        new_password (str): The new password to set

    Returns:
        JSON Response:
            - success: {"message": "Password updated successfully"}, 200
            - error: {"error": error_message}, status_code
    """
    logger.info('Processing password update request')
    data = request.json
    username = data.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not username or not old_password or not new_password:
        logger.error('Missing required fields in password update request')
        return make_response(jsonify({"error": "Username, old password, and new password are required"}), 400)
    
    try:
        if Users.check_password(username, old_password):
            Users.update_password(username, new_password)
            logger.info(f"Password updated successfully for user: {username}")
            return make_response(jsonify({"message": "Password updated successfully"}), 200)
        logger.warning(f"Invalid old password provided for user: {username}")
        return make_response(jsonify({"error": "Invalid old password"}), 401)
    except ValueError as e:
        logger.error(f"Value error during password update: {str(e)}")
        return make_response(jsonify({"error": str(e)}), 404)
    except Exception as e:
        logger.error(f"Unexpected error during password update: {str(e)}")
        return make_response(jsonify({"error": "An error occurred while updating the password"}), 500)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")
    app.run(debug=True)