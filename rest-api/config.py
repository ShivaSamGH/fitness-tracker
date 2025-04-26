import os
import datetime
from constants import AppConfig, UserRole

class Config:
    """
    Configuration settings for the Flask application.

    Attributes:
        SECRET_KEY (str): Secret key for Flask sessions and CSRF protection
        SQLALCHEMY_DATABASE_URI (str): Database connection URI
        SQLALCHEMY_TRACK_MODIFICATIONS (bool): Flag to track modifications of objects
        JWT_SECRET_KEY (str): Secret key for JWT token encoding/decoding
        JWT_ACCESS_TOKEN_EXPIRES (timedelta): Expiration time for JWT tokens
        ALLOWED_ROLES (list): List of allowed user roles in the application
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or AppConfig.DEFAULT_SECRET_KEY

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or AppConfig.DEFAULT_DB_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or AppConfig.DEFAULT_JWT_SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(hours=1)

    ALLOWED_ROLES = UserRole.ALLOWED_ROLES
