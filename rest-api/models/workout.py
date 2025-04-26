"""
Workout model for the Fitness Tracker application.

This file contains the Workout model for storing workout information.
"""

from datetime import datetime
from models.user import db, User
from constants import Database

class Workout(db.Model):
    """
    Workout model for storing workout related details.

    Attributes:
        id (int): Primary key for the workout
        name (str): Name of the workout
        exercise (str): Exercise to be performed
        duration (int): Duration of the workout in minutes
        type (str): Type of workout (e.g., 'Cardio', 'Strength')
        description (str): Description of the workout
        trainer_id (int): ID of the trainer who created the workout
        created_at (datetime): Timestamp when the workout was created
        trainer (relationship): The trainer who created the workout
    """
    __tablename__ = Database.WORKOUTS_TABLE

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(Database.NAME_SIZE), nullable=False)
    exercise = db.Column(db.String(Database.EXERCISE_SIZE), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    type = db.Column(db.String(Database.TYPE_SIZE), nullable=False)
    description = db.Column(db.String(Database.DESCRIPTION_SIZE))
    trainer_id = db.Column(db.Integer, db.ForeignKey(f'{Database.USERS_TABLE}.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    trainer = db.relationship('User', foreign_keys=[trainer_id])

    def __init__(self, name, exercise, duration, type, description, trainer_id):
        """
        Initialize a new Workout instance.

        Args:
            name (str): The name of the workout
            exercise (str): The exercise to be performed
            duration (int): The duration of the workout in minutes
            type (str): The type of workout
            description (str): The description of the workout
            trainer_id (int): The ID of the trainer who created the workout
        """
        self.name = name
        self.exercise = exercise
        self.duration = duration
        self.type = type
        self.description = description
        self.trainer_id = trainer_id

    def to_dict(self):
        """
        Convert the workout object to a dictionary for serialization.

        Returns:
            dict: Dictionary representation of the workout
        """
        return {
            Database.ID_KEY: self.id,
            Database.NAME_KEY: self.name,
            Database.EXERCISE_KEY: self.exercise,
            Database.DURATION_KEY: self.duration,
            Database.TYPE_KEY: self.type,
            Database.DESCRIPTION_KEY: self.description,
            'trainer_id': self.trainer_id,
            Database.CREATED_AT_KEY: self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        """
        String representation of the Workout object.

        Returns:
            str: String representation
        """
        return f'<Workout {self.name}, Exercise: {self.exercise}, Type: {self.type}>'
