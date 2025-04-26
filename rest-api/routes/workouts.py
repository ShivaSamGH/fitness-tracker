"""
Workout management routes for the Fitness Tracker application.

This file contains routes for creating and managing workouts.
"""

from flask import Blueprint, request, jsonify
from flask_restx import Namespace, Resource, fields
from models import db, Workout, User
from routes.auth import token_required
from utils import trainer_required
from constants import StatusCode, Message, API, Database, UserRole

workouts_bp = Blueprint('workouts', __name__)

# Create a namespace for workout routes
workouts_ns = Namespace('workouts', description='Workout operations')

# Define models for request and response payloads
workout_model = workouts_ns.model('Workout', {
    Database.ID_KEY: fields.Integer(readonly=True, description='The workout identifier'),
    Database.NAME_KEY: fields.String(required=True, description='The workout name'),
    Database.EXERCISE_KEY: fields.String(required=True, description='The exercise to be performed'),
    Database.DURATION_KEY: fields.Integer(required=True, description='The duration of the workout in minutes'),
    Database.TYPE_KEY: fields.String(required=True, description='The type of workout'),
    Database.DESCRIPTION_KEY: fields.String(description='The workout description'),
    'trainer_id': fields.Integer(readonly=True, description='The trainer identifier'),
    Database.CREATED_AT_KEY: fields.DateTime(readonly=True, description='Timestamp when the workout was created')
})

create_workout_model = workouts_ns.model('CreateWorkoutRequest', {
    Database.NAME_KEY: fields.String(required=True, description='The workout name'),
    Database.EXERCISE_KEY: fields.String(required=True, description='The exercise to be performed'),
    Database.DURATION_KEY: fields.Integer(required=True, description='The duration of the workout in minutes'),
    Database.TYPE_KEY: fields.String(required=True, description='The type of workout'),
    Database.DESCRIPTION_KEY: fields.String(description='The workout description')
})

response_model = workouts_ns.model('Response', {
    'message': fields.String(required=True, description='Response message'),
    'workout': fields.Nested(workout_model, description='Workout information')
})

@workouts_ns.route(API.CREATE_WORKOUT_ROUTE)
class WorkoutResource(Resource):
    """Endpoint for workout management"""

    @workouts_ns.doc('create_workout')
    @workouts_ns.expect(create_workout_model)
    @workouts_ns.response(StatusCode.CREATED, Message.WORKOUT_CREATED, response_model)
    @workouts_ns.response(StatusCode.BAD_REQUEST, Message.MISSING_FIELDS)
    @workouts_ns.response(StatusCode.UNAUTHORIZED, Message.UNAUTHORIZED_ROLE)
    @token_required
    @trainer_required
    def post(self, current_user):
        """
        Create a new workout.

        Creates a new workout with the provided details.
        Only users with the Trainer role can create workouts.
        """
        data = request.get_json()

        if not data or not data.get(Database.NAME_KEY) or not data.get(Database.EXERCISE_KEY) or \
           not data.get(Database.DURATION_KEY) or not data.get(Database.TYPE_KEY):
            return {'message': Message.MISSING_FIELDS}, StatusCode.BAD_REQUEST

        new_workout = Workout(
            name=data.get(Database.NAME_KEY),
            exercise=data.get(Database.EXERCISE_KEY),
            duration=data.get(Database.DURATION_KEY),
            type=data.get(Database.TYPE_KEY),
            description=data.get(Database.DESCRIPTION_KEY, ''),
            trainer_id=current_user.id
        )
        
        db.session.add(new_workout)
        db.session.commit()

        return {'message': Message.WORKOUT_CREATED, 'workout': new_workout.to_dict()}, StatusCode.CREATED

    @workouts_ns.doc('get_workouts')
    @workouts_ns.response(StatusCode.OK, 'Workouts retrieved')
    @token_required
    def get(self, current_user):
        """
        Get all workouts.

        Retrieves all workouts. If the user is a trainer, only returns workouts created by that trainer.
        If the user is a trainee, returns all workouts.
        """
        if current_user.role == UserRole.TRAINER:
            workouts = Workout.query.filter_by(trainer_id=current_user.id).all()
        else:
            workouts = Workout.query.all()

        return {'workouts': [workout.to_dict() for workout in workouts]}, StatusCode.OK

@workouts_ns.route(API.GET_WORKOUT_ROUTE)
@workouts_ns.param('workout_id', 'The workout identifier')
class WorkoutDetailResource(Resource):
    """Endpoint for viewing workout details"""

    @workouts_ns.doc('get_workout')
    @workouts_ns.response(StatusCode.OK, 'Workout retrieved', response_model)
    @workouts_ns.response(StatusCode.NOT_FOUND, Message.WORKOUT_NOT_FOUND)
    @token_required
    def get(self, current_user, workout_id):
        """
        Get a specific workout.

        Retrieves the details of a specific workout.
        """
        workout = Workout.query.get(workout_id)
        if not workout:
            return {'message': Message.WORKOUT_NOT_FOUND}, StatusCode.NOT_FOUND

        return {'workout': workout.to_dict()}, StatusCode.OK

# Blueprint routes for backward compatibility
@workouts_bp.route(API.CREATE_WORKOUT_ROUTE, methods=['POST'])
@token_required
@trainer_required
def create_workout(current_user):
    """
    Create a new workout.

    Creates a new workout with the provided details.
    Only users with the Trainer role can create workouts.

    Returns:
        201: Workout created successfully
        400: Missing required fields
        401: Unauthorized role
    """
    data = request.get_json()

    if not data or not data.get(Database.NAME_KEY) or not data.get(Database.EXERCISE_KEY) or \
       not data.get(Database.DURATION_KEY) or not data.get(Database.TYPE_KEY):
        return jsonify({'message': Message.MISSING_FIELDS}), StatusCode.BAD_REQUEST

    new_workout = Workout(
        name=data.get(Database.NAME_KEY),
        exercise=data.get(Database.EXERCISE_KEY),
        duration=data.get(Database.DURATION_KEY),
        type=data.get(Database.TYPE_KEY),
        description=data.get(Database.DESCRIPTION_KEY, ''),
        trainer_id=current_user.id
    )
    
    db.session.add(new_workout)
    db.session.commit()

    return jsonify({'message': Message.WORKOUT_CREATED, 'workout': new_workout.to_dict()}), StatusCode.CREATED

@workouts_bp.route(API.CREATE_WORKOUT_ROUTE, methods=['GET'])
@token_required
def get_workouts(current_user):
    """
    Get all workouts.

    Retrieves all workouts. If the user is a trainer, only returns workouts created by that trainer.
    If the user is a trainee, returns all workouts.

    Returns:
        200: Workouts retrieved successfully
    """
    if current_user.role == UserRole.TRAINER:
        workouts = Workout.query.filter_by(trainer_id=current_user.id).all()
    else:
        workouts = Workout.query.all()

    return jsonify({'workouts': [workout.to_dict() for workout in workouts]}), StatusCode.OK

@workouts_bp.route(API.GET_WORKOUT_ROUTE, methods=['GET'])
@token_required
def get_workout(current_user, workout_id):
    """
    Get a specific workout.

    Retrieves the details of a specific workout.

    Returns:
        200: Workout retrieved successfully
        404: Workout not found
    """
    workout = Workout.query.get(workout_id)
    if not workout:
        return jsonify({'message': Message.WORKOUT_NOT_FOUND}), StatusCode.NOT_FOUND

    return jsonify({'workout': workout.to_dict()}), StatusCode.OK
