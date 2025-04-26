from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from constants import Database, UserRole, PASSWORD_KEY, USERNAME_KEY, ROLE_KEY

db = SQLAlchemy()

class User(db.Model):
    """
    User model for storing user related details.

    Attributes:
        id (int): Primary key for the user
        username (str): Unique username for the user
        password_hash (str): Hashed password for the user
        role (str): Role of the user (e.g., 'Trainer', 'Trainee')
        created_at (datetime): Timestamp when the user was created
    """
    __tablename__ = Database.USERS_TABLE

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(Database.USERNAME_SIZE), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(Database.PASSWORD_HASH_SIZE), nullable=False)
    role = db.Column(db.String(Database.ROLE_SIZE), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, username, password, role):
        """
        Initialize a new User instance.

        Args:
            username (str): The username for the user
            password (str): The plain text password that will be hashed
            role (str): The role of the user
        """
        self.username = username
        self.set_password(password)
        self.role = role

    def set_password(self, password):
        """
        Set the password hash from a plain text password.

        Args:
            password (str): The plain text password to hash
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Check if the provided password matches the stored hash.

        Args:
            password (str): The plain text password to check

        Returns:
            bool: True if the password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """
        Convert the user object to a dictionary for serialization.

        Returns:
            dict: Dictionary representation of the user
        """
        return {
            Database.ID_KEY: self.id,
            Database.USERNAME_KEY: self.username,
            Database.ROLE_KEY: self.role,
            Database.CREATED_AT_KEY: self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        """
        String representation of the User object.

        Returns:
            str: String representation
        """
        return f'<User {self.username}, Role: {self.role}>'
