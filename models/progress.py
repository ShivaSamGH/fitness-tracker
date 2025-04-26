"""
Progress model for the Fitness Tracker application.

This file contains the Progress model for tracking workout progress.
"""

from datetime import datetime
from models.user import db, User
from models.workout import Workout
from constants import Database

class Progress(db.Model):
    """
    Progress model for storing workout progress details.

    Attributes:
        id (int): Primary key for the progress entry
        user_id (int): ID of the user who logged the progress
        workout_id (int): ID of the workout for which progress is logged
        value (float): Value of the progress (e.g., weight lifted, distance covered)
        date (datetime): Date when the progress was logged
        notes (str): Additional notes about the progress
        created_at (datetime): Timestamp when the progress entry was created
        user (relationship): The user who logged the progress
        workout (relationship): The workout for which progress is logged
    """
    __tablename__ = Database.PROGRESS_TABLE

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(f'{Database.USERS_TABLE}.id'), nullable=False)
    workout_id = db.Column(db.Integer, db.ForeignKey(f'{Database.WORKOUTS_TABLE}.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    notes = db.Column(db.String(Database.DESCRIPTION_SIZE))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    workout = db.relationship('Workout', foreign_keys=[workout_id])

    def __init__(self, user_id, workout_id, value, date=None, notes=None):
        """
        Initialize a new Progress instance.

        Args:
            user_id (int): The ID of the user who logged the progress
            workout_id (int): The ID of the workout for which progress is logged
            value (float): The value of the progress
            date (date, optional): The date when the progress was logged
            notes (str, optional): Additional notes about the progress
        """
        self.user_id = user_id
        self.workout_id = workout_id
        self.value = value
        self.date = date if date else datetime.utcnow().date()
        self.notes = notes

    def to_dict(self):
        """
        Convert the progress object to a dictionary for serialization.

        Returns:
            dict: Dictionary representation of the progress
        """
        return {
            Database.ID_KEY: self.id,
            Database.USER_ID_KEY: self.user_id,
            Database.WORKOUT_ID_KEY: self.workout_id,
            Database.VALUE_KEY: self.value,
            Database.DATE_KEY: self.date.isoformat() if self.date else None,
            Database.DESCRIPTION_KEY: self.notes,
            Database.CREATED_AT_KEY: self.created_at.isoformat() if self.created_at else None,
            'workout': self.workout.to_dict() if self.workout else None
        }

    def __repr__(self):
        """
        String representation of the Progress object.

        Returns:
            str: String representation
        """
        return f'<Progress User ID: {self.user_id}, Workout ID: {self.workout_id}, Value: {self.value}>'
