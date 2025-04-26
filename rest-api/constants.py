"""
Constants for the Fitness Tracker application.

This file contains all the constants used throughout the application,
organized into logical categories for better maintainability.
"""

# HTTP Status Codes
class StatusCode:
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500

# API Configuration
class API:
    VERSION = '1.0'
    TITLE = 'Fitness Tracker API'
    DESCRIPTION = 'A RESTful API for tracking fitness activities'
    DOCS_URL = '/api/docs'
    PREFIX = '/api'

    # Auth namespace
    AUTH_PATH = '/auth'
    AUTH_URL_PREFIX = '/api/auth'

    # Groups namespace
    GROUPS_PATH = '/groups'
    GROUPS_URL_PREFIX = '/api/groups'

    # Workouts namespace
    WORKOUTS_PATH = '/workouts'
    WORKOUTS_URL_PREFIX = '/api/workouts'

    # Workout Plans namespace
    WORKOUT_PLANS_PATH = '/workout-plans'
    WORKOUT_PLANS_URL_PREFIX = '/api/workout-plans'

    # Progress namespace
    PROGRESS_PATH = '/progress'
    PROGRESS_URL_PREFIX = '/api/progress'

    # Routes
    # Auth routes
    SIGNUP_ROUTE = '/signup'
    SIGNIN_ROUTE = '/signin'

    # Group routes
    CREATE_GROUP_ROUTE = ''
    JOIN_GROUP_ROUTE = '/join'
    GROUP_INVITE_ROUTE = '/<int:group_id>/invite'
    GROUP_MEMBERS_ROUTE = '/<int:group_id>/members'

    # Workout routes
    CREATE_WORKOUT_ROUTE = ''
    GET_WORKOUT_ROUTE = '/<int:workout_id>'

    # Workout Plan routes
    CREATE_WORKOUT_PLAN_ROUTE = ''
    GET_WORKOUT_PLAN_ROUTE = '/<int:workout_plan_id>'
    ADD_WORKOUT_TO_PLAN_ROUTE = '/<int:workout_plan_id>/workouts'
    ASSIGN_PLAN_TO_GROUP_ROUTE = '/<int:workout_plan_id>/assign'

    # Progress routes
    LOG_PROGRESS_ROUTE = ''
    GET_PROGRESS_ROUTE = '/<int:progress_id>'
    GET_USER_PROGRESS_ROUTE = '/user'

    # Content types
    CONTENT_TYPE_JSON = 'application/json'

# Messages
class Message:
    # Success messages
    USER_CREATED = 'User created successfully'
    LOGIN_SUCCESSFUL = 'Login successful'
    GROUP_CREATED = 'Group created successfully'
    WORKOUT_CREATED = 'Workout created successfully'
    WORKOUT_PLAN_CREATED = 'Workout plan created successfully'
    PROGRESS_LOGGED = 'Progress logged successfully'
    INVITE_CREATED = 'Invite created successfully'
    JOINED_GROUP = 'Joined group successfully'
    WORKOUT_ADDED_TO_PLAN = 'Workout added to plan successfully'
    PLAN_ASSIGNED_TO_GROUP = 'Workout plan assigned to group successfully'

    # Error messages
    MISSING_FIELDS = 'Missing required fields'
    USERNAME_EXISTS = 'Username already exists'
    INVALID_CREDENTIALS = 'Invalid username or password'
    TOKEN_MISSING = 'Token is missing'
    TOKEN_INVALID = 'Token is invalid'
    RESOURCE_NOT_FOUND = 'Resource not found'
    INTERNAL_SERVER_ERROR = 'Internal server error'
    UNAUTHORIZED_ROLE = 'User role not authorized for this action'
    INVALID_INVITE_CODE = 'Invalid invite code'
    ALREADY_MEMBER = 'User is already a member of this group'
    GROUP_NOT_FOUND = 'Group not found'
    WORKOUT_NOT_FOUND = 'Workout not found'
    WORKOUT_PLAN_NOT_FOUND = 'Workout plan not found'
    PROGRESS_NOT_FOUND = 'Progress not found'

    # Format strings
    INVALID_ROLE_FORMAT = 'Invalid role. Allowed roles: {}'

    # Message fragments
    INVALID_ROLE = 'Invalid role'

# JWT Configuration
class JWT:
    COOKIE_NAME = 'jwt'
    ALGORITHM = 'HS256'

    # Token payload fields
    USER_ID_FIELD = 'user_id'
    USERNAME_FIELD = 'username'
    ROLE_FIELD = 'role'
    EXPIRATION_FIELD = 'exp'

# Application Configuration
class AppConfig:
    DEBUG = True
    ROOT_MESSAGE = 'Fitness Tracker API'

    # Default secret keys
    DEFAULT_SECRET_KEY = 'dev-secret-key'
    DEFAULT_JWT_SECRET_KEY = 'jwt-secret-key'

    # Database
    DEFAULT_DB_URI = 'sqlite:///fitness_tracker.db'
    TEST_DB_URI = 'sqlite:///:memory:'

# HTTP Methods
class HttpMethod:
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'

# Database Configuration
class Database:
    # Tables
    USERS_TABLE = 'users'
    GROUPS_TABLE = 'groups'
    WORKOUTS_TABLE = 'workouts'
    WORKOUT_PLANS_TABLE = 'workout_plans'
    PROGRESS_TABLE = 'progress'
    GROUP_MEMBERS_TABLE = 'group_members'
    WORKOUT_PLAN_WORKOUTS_TABLE = 'workout_plan_workouts'
    GROUP_WORKOUT_PLANS_TABLE = 'group_workout_plans'

    # Column sizes
    USERNAME_SIZE = 64
    PASSWORD_HASH_SIZE = 128
    ROLE_SIZE = 20
    NAME_SIZE = 100
    DESCRIPTION_SIZE = 500
    EXERCISE_SIZE = 100
    TYPE_SIZE = 50
    INVITE_CODE_SIZE = 20

    # Dictionary keys
    ID_KEY = 'id'
    USERNAME_KEY = 'username'
    PASSWORD_KEY = 'password'
    PASSWORD_HASH_KEY = 'password_hash'
    ROLE_KEY = 'role'
    CREATED_AT_KEY = 'created_at'
    NAME_KEY = 'name'
    DESCRIPTION_KEY = 'description'
    EXERCISE_KEY = 'exercise'
    DURATION_KEY = 'duration'
    TYPE_KEY = 'type'
    INVITE_CODE_KEY = 'invite_code'
    GROUP_ID_KEY = 'group_id'
    WORKOUT_ID_KEY = 'workout_id'
    WORKOUT_PLAN_ID_KEY = 'workout_plan_id'
    USER_ID_KEY = 'user_id'
    ORDER_KEY = 'order'
    VALUE_KEY = 'value'
    DATE_KEY = 'date'

# User Roles
class UserRole:
    TRAINER = 'Trainer'
    TRAINEE = 'Trainee'
    ALLOWED_ROLES = [TRAINER, TRAINEE]
    INVALID_ROLE = 'InvalidRole'

# Test Data
class TestData:
    # Test usernames
    TEST_USERNAME = 'test'
    TRAINER_USERNAME = 'trainer1'
    TRAINEE_USERNAME = 'trainee1'
    USER_USERNAME = 'user1'
    EXISTING_USERNAME = 'existing_user'
    TEST_USER_USERNAME = 'test_user'
    NON_EXISTENT_USERNAME = 'non_existent_user'

    # Test passwords
    PASSWORD = 'password'
    PASSWORD_123 = 'password123'
    WRONG_PASSWORD = 'wrong_password'

# Field names
USERNAME_KEY = Database.USERNAME_KEY
PASSWORD_KEY = Database.PASSWORD_KEY
ROLE_KEY = Database.ROLE_KEY
