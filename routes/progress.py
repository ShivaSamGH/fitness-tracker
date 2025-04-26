"""
Progress tracking routes for the Fitness Tracker application.

This file contains routes for logging and viewing workout progress.
"""

from flask import Blueprint, request, jsonify
from flask_restx import Namespace, Resource, fields
from models import db, Progress, Workout, User, Group
from routes.auth import token_required
from utils import trainee_required
from constants import StatusCode, Message, API, Database, UserRole
from datetime import datetime

progress_bp = Blueprint('progress', __name__)

# Create a namespace for progress routes
progress_ns = Namespace('progress', description='Progress tracking operations')

# Define models for request and response payloads
workout_model = progress_ns.model('Workout', {
    Database.ID_KEY: fields.Integer(readonly=True, description='The workout identifier'),
    Database.NAME_KEY: fields.String(required=True, description='The workout name'),
    Database.EXERCISE_KEY: fields.String(required=True, description='The exercise to be performed'),
    Database.DURATION_KEY: fields.Integer(required=True, description='The duration of the workout in minutes'),
    Database.TYPE_KEY: fields.String(required=True, description='The type of workout'),
    Database.DESCRIPTION_KEY: fields.String(description='The workout description')
})

progress_model = progress_ns.model('Progress', {
    Database.ID_KEY: fields.Integer(readonly=True, description='The progress identifier'),
    Database.USER_ID_KEY: fields.Integer(readonly=True, description='The user identifier'),
    Database.WORKOUT_ID_KEY: fields.Integer(required=True, description='The workout identifier'),
    Database.VALUE_KEY: fields.Float(required=True, description='The progress value'),
    Database.DATE_KEY: fields.Date(description='The date of the progress'),
    Database.DESCRIPTION_KEY: fields.String(description='Notes about the progress'),
    Database.CREATED_AT_KEY: fields.DateTime(readonly=True, description='Timestamp when the progress was logged'),
    'workout': fields.Nested(workout_model, description='Workout information')
})

log_progress_model = progress_ns.model('LogProgressRequest', {
    Database.WORKOUT_ID_KEY: fields.Integer(required=True, description='The workout identifier'),
    Database.VALUE_KEY: fields.Float(required=True, description='The progress value'),
    Database.DATE_KEY: fields.Date(description='The date of the progress'),
    Database.DESCRIPTION_KEY: fields.String(description='Notes about the progress')
})

response_model = progress_ns.model('Response', {
    'message': fields.String(required=True, description='Response message'),
    'progress': fields.Nested(progress_model, description='Progress information')
})

@progress_ns.route(API.LOG_PROGRESS_ROUTE)
class ProgressResource(Resource):
    """Endpoint for progress tracking"""

    @progress_ns.doc('log_progress')
    @progress_ns.expect(log_progress_model)
    @progress_ns.response(StatusCode.CREATED, Message.PROGRESS_LOGGED, response_model)
    @progress_ns.response(StatusCode.BAD_REQUEST, Message.MISSING_FIELDS)
    @progress_ns.response(StatusCode.NOT_FOUND, Message.WORKOUT_NOT_FOUND)
    @progress_ns.response(StatusCode.UNAUTHORIZED, Message.UNAUTHORIZED_ROLE)
    @token_required
    @trainee_required
    def post(self, current_user):
        """
        Log workout progress.

        Logs progress for a specific workout.
        Only users with the Trainee role can log progress.
        """
        data = request.get_json()

        if not data or not data.get(Database.WORKOUT_ID_KEY) or not data.get(Database.VALUE_KEY):
            return {'message': Message.MISSING_FIELDS}, StatusCode.BAD_REQUEST

        workout = Workout.query.get(data.get(Database.WORKOUT_ID_KEY))
        if not workout:
            return {'message': Message.WORKOUT_NOT_FOUND}, StatusCode.NOT_FOUND

        # Parse date if provided, otherwise use current date
        date = None
        if data.get(Database.DATE_KEY):
            try:
                date = datetime.fromisoformat(data.get(Database.DATE_KEY)).date()
            except ValueError:
                return {'message': 'Invalid date format. Use ISO format (YYYY-MM-DD).'}, StatusCode.BAD_REQUEST

        new_progress = Progress(
            user_id=current_user.id,
            workout_id=data.get(Database.WORKOUT_ID_KEY),
            value=data.get(Database.VALUE_KEY),
            date=date,
            notes=data.get(Database.DESCRIPTION_KEY)
        )

        db.session.add(new_progress)
        db.session.commit()

        return {'message': Message.PROGRESS_LOGGED, 'progress': new_progress.to_dict()}, StatusCode.CREATED

    @progress_ns.doc('get_all_progress')
    @progress_ns.response(StatusCode.OK, 'Progress entries retrieved')
    @token_required
    def get(self, current_user):
        """
        Get all progress entries.

        Retrieves all progress entries for the current user.
        If the user is a trainer, they can see progress for all trainees in their groups.
        """
        if current_user.role == UserRole.TRAINEE:
            # Trainees can only see their own progress
            progress_entries = Progress.query.filter_by(user_id=current_user.id).all()
        else:
            # Trainers can see progress for all trainees in their groups
            trainee_ids = []
            for group in Group.query.filter_by(trainer_id=current_user.id).all():
                for member in group.members:
                    if member.role == UserRole.TRAINEE:
                        trainee_ids.append(member.id)

            # Remove duplicates
            trainee_ids = list(set(trainee_ids))

            if trainee_ids:
                progress_entries = Progress.query.filter(Progress.user_id.in_(trainee_ids)).all()
            else:
                progress_entries = []

        return {'progress_entries': [entry.to_dict() for entry in progress_entries]}, StatusCode.OK

@progress_ns.route(API.GET_PROGRESS_ROUTE)
@progress_ns.param('progress_id', 'The progress identifier')
class ProgressDetailResource(Resource):
    """Endpoint for viewing progress details"""

    @progress_ns.doc('get_progress')
    @progress_ns.response(StatusCode.OK, 'Progress retrieved', response_model)
    @progress_ns.response(StatusCode.NOT_FOUND, Message.PROGRESS_NOT_FOUND)
    @progress_ns.response(StatusCode.UNAUTHORIZED, Message.UNAUTHORIZED_ROLE)
    @token_required
    def get(self, current_user, progress_id):
        """
        Get a specific progress entry.

        Retrieves the details of a specific progress entry.
        Users can only view their own progress or, for trainers, progress of trainees in their groups.
        """
        progress = Progress.query.get(progress_id)
        if not progress:
            return {'message': Message.PROGRESS_NOT_FOUND}, StatusCode.NOT_FOUND

        # Check if the user is authorized to view this progress
        if current_user.role == UserRole.TRAINEE and progress.user_id != current_user.id:
            return {'message': Message.UNAUTHORIZED_ROLE}, StatusCode.UNAUTHORIZED

        if current_user.role == UserRole.TRAINER:
            # Check if the progress belongs to a trainee in one of the trainer's groups
            trainee_ids = []
            for group in Group.query.filter_by(trainer_id=current_user.id).all():
                for member in group.members:
                    if member.role == UserRole.TRAINEE:
                        trainee_ids.append(member.id)

            if progress.user_id not in trainee_ids:
                return {'message': Message.UNAUTHORIZED_ROLE}, StatusCode.UNAUTHORIZED

        return {'progress': progress.to_dict()}, StatusCode.OK

@progress_ns.route(API.GET_USER_PROGRESS_ROUTE)
class UserProgressResource(Resource):
    """Endpoint for viewing user's progress"""

    @progress_ns.doc('get_user_progress')
    @progress_ns.response(StatusCode.OK, 'User progress retrieved')
    @token_required
    def get(self, current_user):
        """
        Get progress for the current user.

        Retrieves all progress entries for the current user.
        """
        progress_entries = Progress.query.filter_by(user_id=current_user.id).all()
        return {'progress_entries': [entry.to_dict() for entry in progress_entries]}, StatusCode.OK

# Blueprint routes for backward compatibility
@progress_bp.route(API.LOG_PROGRESS_ROUTE, methods=['POST'])
@token_required
@trainee_required
def log_progress(current_user):
    """
    Log workout progress.

    Logs progress for a specific workout.
    Only users with the Trainee role can log progress.

    Returns:
        201: Progress logged successfully
        400: Missing required fields
        401: Unauthorized role
        404: Workout not found
    """
    data = request.get_json()

    if not data or not data.get(Database.WORKOUT_ID_KEY) or not data.get(Database.VALUE_KEY):
        return jsonify({'message': Message.MISSING_FIELDS}), StatusCode.BAD_REQUEST

    workout = Workout.query.get(data.get(Database.WORKOUT_ID_KEY))
    if not workout:
        return jsonify({'message': Message.WORKOUT_NOT_FOUND}), StatusCode.NOT_FOUND

    # Parse date if provided, otherwise use current date
    date = None
    if data.get(Database.DATE_KEY):
        try:
            date = datetime.fromisoformat(data.get(Database.DATE_KEY)).date()
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use ISO format (YYYY-MM-DD).'}), StatusCode.BAD_REQUEST

    new_progress = Progress(
        user_id=current_user.id,
        workout_id=data.get(Database.WORKOUT_ID_KEY),
        value=data.get(Database.VALUE_KEY),
        date=date,
        notes=data.get(Database.DESCRIPTION_KEY)
    )

    db.session.add(new_progress)
    db.session.commit()

    return jsonify({'message': Message.PROGRESS_LOGGED, 'progress': new_progress.to_dict()}), StatusCode.CREATED

@progress_bp.route(API.LOG_PROGRESS_ROUTE, methods=['GET'])
@token_required
def get_all_progress(current_user):
    """
    Get all progress entries.

    Retrieves all progress entries for the current user.
    If the user is a trainer, they can see progress for all trainees in their groups.

    Returns:
        200: Progress entries retrieved successfully
    """
    if current_user.role == UserRole.TRAINEE:
        # Trainees can only see their own progress
        progress_entries = Progress.query.filter_by(user_id=current_user.id).all()
    else:
        # Trainers can see progress for all trainees in their groups
        from models import Group
        trainee_ids = []
        for group in Group.query.filter_by(trainer_id=current_user.id).all():
            for member in group.members:
                if member.role == UserRole.TRAINEE:
                    trainee_ids.append(member.id)

        # Remove duplicates
        trainee_ids = list(set(trainee_ids))

        if trainee_ids:
            progress_entries = Progress.query.filter(Progress.user_id.in_(trainee_ids)).all()
        else:
            progress_entries = []

    return jsonify({'progress_entries': [entry.to_dict() for entry in progress_entries]}), StatusCode.OK

@progress_bp.route(API.GET_PROGRESS_ROUTE, methods=['GET'])
@token_required
def get_progress(current_user, progress_id):
    """
    Get a specific progress entry.

    Retrieves the details of a specific progress entry.
    Users can only view their own progress or, for trainers, progress of trainees in their groups.

    Returns:
        200: Progress retrieved successfully
        401: Unauthorized role
        404: Progress not found
    """
    progress = Progress.query.get(progress_id)
    if not progress:
        return jsonify({'message': Message.PROGRESS_NOT_FOUND}), StatusCode.NOT_FOUND

    # Check if the user is authorized to view this progress
    if current_user.role == UserRole.TRAINEE and progress.user_id != current_user.id:
        return jsonify({'message': Message.UNAUTHORIZED_ROLE}), StatusCode.UNAUTHORIZED

    if current_user.role == UserRole.TRAINER:
        # Check if the progress belongs to a trainee in one of the trainer's groups
        from models import Group
        trainee_ids = []
        for group in Group.query.filter_by(trainer_id=current_user.id).all():
            for member in group.members:
                if member.role == UserRole.TRAINEE:
                    trainee_ids.append(member.id)

        if progress.user_id not in trainee_ids:
            return jsonify({'message': Message.UNAUTHORIZED_ROLE}), StatusCode.UNAUTHORIZED

    return jsonify({'progress': progress.to_dict()}), StatusCode.OK

@progress_bp.route(API.GET_USER_PROGRESS_ROUTE, methods=['GET'])
@token_required
def get_user_progress(current_user):
    """
    Get progress for the current user.

    Retrieves all progress entries for the current user.

    Returns:
        200: User progress retrieved successfully
    """
    progress_entries = Progress.query.filter_by(user_id=current_user.id).all()
    return jsonify({'progress_entries': [entry.to_dict() for entry in progress_entries]}), StatusCode.OK
