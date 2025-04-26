"""
WorkoutPlan model for the Fitness Tracker application.

This file contains the WorkoutPlan model and related association tables.
"""

from datetime import datetime
from models.user import db, User
from models.workout import Workout
from models.group import Group
from constants import Database

# Association table for workout plan workouts
workout_plan_workouts = db.Table(
    Database.WORKOUT_PLAN_WORKOUTS_TABLE,
    db.Column('workout_plan_id', db.Integer, db.ForeignKey(f'{Database.WORKOUT_PLANS_TABLE}.id'), primary_key=True),
    db.Column('workout_id', db.Integer, db.ForeignKey(f'{Database.WORKOUTS_TABLE}.id'), primary_key=True),
    db.Column('order', db.Integer, nullable=False)
)

# Association table for group workout plans
group_workout_plans = db.Table(
    Database.GROUP_WORKOUT_PLANS_TABLE,
    db.Column('group_id', db.Integer, db.ForeignKey(f'{Database.GROUPS_TABLE}.id'), primary_key=True),
    db.Column('workout_plan_id', db.Integer, db.ForeignKey(f'{Database.WORKOUT_PLANS_TABLE}.id'), primary_key=True)
)

class WorkoutPlan(db.Model):
    """
    WorkoutPlan model for storing workout plan related details.

    Attributes:
        id (int): Primary key for the workout plan
        name (str): Name of the workout plan
        description (str): Description of the workout plan
        trainer_id (int): ID of the trainer who created the workout plan
        created_at (datetime): Timestamp when the workout plan was created
        trainer (relationship): The trainer who created the workout plan
        workouts (relationship): Workouts included in the plan
        groups (relationship): Groups assigned to this workout plan
    """
    __tablename__ = Database.WORKOUT_PLANS_TABLE

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(Database.NAME_SIZE), nullable=False)
    description = db.Column(db.String(Database.DESCRIPTION_SIZE))
    trainer_id = db.Column(db.Integer, db.ForeignKey(f'{Database.USERS_TABLE}.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    trainer = db.relationship('User', foreign_keys=[trainer_id])
    workouts = db.relationship('Workout', secondary=workout_plan_workouts, lazy='subquery',
                              backref=db.backref('workout_plans', lazy=True))
    groups = db.relationship('Group', secondary=group_workout_plans, lazy='subquery',
                            backref=db.backref('workout_plans', lazy=True))

    def __init__(self, name, description, trainer_id):
        """
        Initialize a new WorkoutPlan instance.

        Args:
            name (str): The name of the workout plan
            description (str): The description of the workout plan
            trainer_id (int): The ID of the trainer who created the workout plan
        """
        self.name = name
        self.description = description
        self.trainer_id = trainer_id

    def add_workout(self, workout, order):
        """
        Add a workout to the plan with a specific order.

        Args:
            workout (Workout): The workout to add
            order (int): The order of the workout in the plan
        """
        # This is a custom method to handle the order in the association table
        # We need to use db.session.execute to insert into the association table with the order
        db.session.execute(
            workout_plan_workouts.insert().values(
                workout_plan_id=self.id,
                workout_id=workout.id,
                order=order
            )
        )
        db.session.commit()

    def get_workouts_in_order(self):
        """
        Get the workouts in the plan in order.

        Returns:
            list: List of workouts in order
        """
        # Query the association table to get workouts in order
        result = db.session.query(
            Workout, workout_plan_workouts.c.order
        ).join(
            workout_plan_workouts, Workout.id == workout_plan_workouts.c.workout_id
        ).filter(
            workout_plan_workouts.c.workout_plan_id == self.id
        ).order_by(
            workout_plan_workouts.c.order
        ).all()
        
        return [{'workout': workout.to_dict(), 'order': order} for workout, order in result]

    def to_dict(self):
        """
        Convert the workout plan object to a dictionary for serialization.

        Returns:
            dict: Dictionary representation of the workout plan
        """
        return {
            Database.ID_KEY: self.id,
            Database.NAME_KEY: self.name,
            Database.DESCRIPTION_KEY: self.description,
            'trainer_id': self.trainer_id,
            Database.CREATED_AT_KEY: self.created_at.isoformat() if self.created_at else None,
            'workouts': self.get_workouts_in_order(),
            'groups_count': len(self.groups)
        }

    def __repr__(self):
        """
        String representation of the WorkoutPlan object.

        Returns:
            str: String representation
        """
        return f'<WorkoutPlan {self.name}, Trainer ID: {self.trainer_id}>'
