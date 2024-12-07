#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/api/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
# check_db() {
#   echo "Checking database connection..."
#   curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
#   if [ $? -eq 0 ]; then
#     echo "Database connection is healthy."
#   else
#     echo "Database check failed."
#     exit 1
#   fi
# }

##########################################################
#
# User Management
#
##########################################################

create_account() {
  username=$1
  password=$2

  echo "Creating New Account..."
  curl -s -X POST "$BASE_URL/create-account" -H "Content-Type: application/json" \
    -d "{\"username\":\"$username\", \"password\":\"$password\"}" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Account created successfully."
  else
    echo "Account Creation failed."
    exit 1
  fi
}

login() {
  username=$1
  password=$2

  echo "Logging in..."
  curl -s -X POST "$BASE_URL/login" -H "Content-Type: application/json" \
    -d "{\"username\":\"$username\", \"password\":\"$password\"}" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Login successfully."
  else
    echo "Account Login failed."
    exit 1
  fi
}

update_password() {
  username=$1
  old_password=$2
  new_password=$3

  echo "Logging in..."
  curl -s -X POST "$BASE_URL/update-password" -H "Content-Type: application/json" \
    -d "{\"username\":\"$username\", \"old_password\":\"$old_password\", \"new_password\":\"$new_password\"}" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Password updated successfully."
  else
    echo "Password Update failed."
    exit 1
  fi
}

##########################################################
#
# Movie Management
#
##########################################################

search_by_name(){
  name=$1

  echo "Searching by name..."
  curl -s -X POST "$BASE_URL/movies/search-by-name" -H "Content-Type: application/json" \
    -d "{\"name\":\"$name\"}" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Movie retrived successfully."
  else
    echo "Movie Retrieval failed."
    exit 1
  fi
}

search_by_year(){
  year=$1

  echo "Searching by year..."
  curl -s -X POST "$BASE_URL/movies/search-by-year" -H "Content-Type: application/json" \
    -d "{\"year\":$year}" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Movie retrived successfully."
  else
    echo "Movie Retrieval failed."
    exit 1
  fi
}

search_by_language(){
  language_code=$1

  echo "Searching by language..."
  curl -s -X POST "$BASE_URL/movies/search-by-language" -H "Content-Type: application/json" \
    -d "{\"language_code\":\"$language_code\"}" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Movie retrived successfully."
  else
    echo "Movie Retrieval failed."
    exit 1
  fi
}

search_by_director(){
  director=$1

  echo "Searching by director..."
  curl -s -X POST "$BASE_URL/movies/search-by-director" -H "Content-Type: application/json" \
    -d "{\"director\":\"$director\"}" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Movie retrived successfully."
  else
    echo "Movie Retrieval failed."
    exit 1
  fi
}

search_by_genre(){
  genre_id=$1

  echo "Searching by genre..."
  curl -s -X POST "$BASE_URL/movies/search-by-genre" -H "Content-Type: application/json" \
    -d "{\"genre_id\":\"$genre_id\"}" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Movie retrived successfully."
  else
    echo "Movie Retrieval failed."
    exit 1
  fi
}
    
# Health checks
check_health
# check_db

# User Management
create_account "username" "password"
login "username" "password"
update_password "username" "password" "password123"

# Movie Management
search_by_name "Inception"
search_by_year 2020
search_by_language "en"
search_by_director "Christopher Nolan"
search_by_genre 28

echo "All tests passed successfully!"
