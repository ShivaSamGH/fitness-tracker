"""
Workout Plan management routes for the Fitness Tracker application.

This file contains routes for creating and managing workout plans.
"""

from flask import Blueprint, request, jsonify
from flask_restx import Namespace, Resource, fields
from models import db, WorkoutPlan, Workout, Group
from routes.auth import token_required
from utils import trainer_required
from constants import StatusCode, Message, API, Database, UserRole

workout_plans_bp = Blueprint('workout_plans', __name__)

# Create a namespace for workout plan routes
workout_plans_ns = Namespace('workout-plans', description='Workout Plan operations')

# Define models for request and response payloads
workout_model = workout_plans_ns.model('Workout', {
    Database.ID_KEY: fields.Integer(readonly=True, description='The workout identifier'),
    Database.NAME_KEY: fields.String(required=True, description='The workout name'),
    Database.EXERCISE_KEY: fields.String(required=True, description='The exercise to be performed'),
    Database.DURATION_KEY: fields.Integer(required=True, description='The duration of the workout in minutes'),
    Database.TYPE_KEY: fields.String(required=True, description='The type of workout'),
    Database.DESCRIPTION_KEY: fields.String(description='The workout description')
})

workout_order_model = workout_plans_ns.model('WorkoutOrder', {
    'workout': fields.Nested(workout_model, description='Workout information'),
    Database.ORDER_KEY: fields.Integer(required=True, description='The order of the workout in the plan')
})

workout_plan_model = workout_plans_ns.model('WorkoutPlan', {
    Database.ID_KEY: fields.Integer(readonly=True, description='The workout plan identifier'),
    Database.NAME_KEY: fields.String(required=True, description='The workout plan name'),
    Database.DESCRIPTION_KEY: fields.String(description='The workout plan description'),
    'trainer_id': fields.Integer(readonly=True, description='The trainer identifier'),
    Database.CREATED_AT_KEY: fields.DateTime(readonly=True, description='Timestamp when the workout plan was created'),
    'workouts': fields.List(fields.Nested(workout_order_model), description='Workouts in the plan'),
    'groups_count': fields.Integer(readonly=True, description='Number of groups assigned to the plan')
})

create_workout_plan_model = workout_plans_ns.model('CreateWorkoutPlanRequest', {
    Database.NAME_KEY: fields.String(required=True, description='The workout plan name'),
    Database.DESCRIPTION_KEY: fields.String(description='The workout plan description')
})

add_workout_model = workout_plans_ns.model('AddWorkoutRequest', {
    Database.WORKOUT_ID_KEY: fields.Integer(required=True, description='The workout identifier'),
    Database.ORDER_KEY: fields.Integer(required=True, description='The order of the workout in the plan')
})

assign_plan_model = workout_plans_ns.model('AssignPlanRequest', {
    Database.GROUP_ID_KEY: fields.Integer(required=True, description='The group identifier')
})

response_model = workout_plans_ns.model('Response', {
    'message': fields.String(required=True, description='Response message'),
    'workout_plan': fields.Nested(workout_plan_model, description='Workout plan information')
})

@workout_plans_ns.route(API.CREATE_WORKOUT_PLAN_ROUTE)
class WorkoutPlanResource(Resource):
    """Endpoint for workout plan management"""

    @workout_plans_ns.doc('create_workout_plan')
    @workout_plans_ns.expect(create_workout_plan_model)
    @workout_plans_ns.response(StatusCode.CREATED, Message.WORKOUT_PLAN_CREATED, response_model)
    @workout_plans_ns.response(StatusCode.BAD_REQUEST, Message.MISSING_FIELDS)
    @workout_plans_ns.response(StatusCode.UNAUTHORIZED, Message.UNAUTHORIZED_ROLE)
    @token_required
    @trainer_required
    def post(self, current_user):
        """
        Create a new workout plan.

        Creates a new workout plan with the provided details.
        Only users with the Trainer role can create workout plans.
        """
        data = request.get_json()

        if not data or not data.get(Database.NAME_KEY):
            return {'message': Message.MISSING_FIELDS}, StatusCode.BAD_REQUEST

        new_workout_plan = WorkoutPlan(
            name=data.get(Database.NAME_KEY),
            description=data.get(Database.DESCRIPTION_KEY, ''),
            trainer_id=current_user.id
        )
        
        db.session.add(new_workout_plan)
        db.session.commit()

        return {'message': Message.WORKOUT_PLAN_CREATED, 'workout_plan': new_workout_plan.to_dict()}, StatusCode.CREATED

    @workout_plans_ns.doc('get_workout_plans')
    @workout_plans_ns.response(StatusCode.OK, 'Workout plans retrieved')
    @token_required
    def get(self, current_user):
        """
        Get all workout plans.

        Retrieves all workout plans. If the user is a trainer, only returns workout plans created by that trainer.
        If the user is a trainee, returns workout plans assigned to groups the trainee is a member of.
        """
        if current_user.role == UserRole.TRAINER:
            workout_plans = WorkoutPlan.query.filter_by(trainer_id=current_user.id).all()
        else:
            # For trainees, get workout plans assigned to their groups
            workout_plans = []
            for group in current_user.groups:
                workout_plans.extend(group.workout_plans)
            # Remove duplicates
            workout_plans = list(set(workout_plans))

        return {'workout_plans': [plan.to_dict() for plan in workout_plans]}, StatusCode.OK

@workout_plans_ns.route(API.GET_WORKOUT_PLAN_ROUTE)
@workout_plans_ns.param('workout_plan_id', 'The workout plan identifier')
class WorkoutPlanDetailResource(Resource):
    """Endpoint for viewing workout plan details"""

    @workout_plans_ns.doc('get_workout_plan')
    @workout_plans_ns.response(StatusCode.OK, 'Workout plan retrieved', response_model)
    @workout_plans_ns.response(StatusCode.NOT_FOUND, Message.WORKOUT_PLAN_NOT_FOUND)
    @token_required
    def get(self, current_user, workout_plan_id):
        """
        Get a specific workout plan.

        Retrieves the details of a specific workout plan.
        """
        workout_plan = WorkoutPlan.query.get(workout_plan_id)
        if not workout_plan:
            return {'message': Message.WORKOUT_PLAN_NOT_FOUND}, StatusCode.NOT_FOUND

        # Check if the user is authorized to view this workout plan
        if current_user.role == UserRole.TRAINER and workout_plan.trainer_id != current_user.id:
            return {'message': Message.UNAUTHORIZED_ROLE}, StatusCode.UNAUTHORIZED
        
        if current_user.role == UserRole.TRAINEE:
            # Check if the trainee is a member of any group assigned to this workout plan
            user_groups = set(current_user.groups)
            plan_groups = set(workout_plan.groups)
            if not user_groups.intersection(plan_groups):
                return {'message': Message.UNAUTHORIZED_ROLE}, StatusCode.UNAUTHORIZED

        return {'workout_plan': workout_plan.to_dict()}, StatusCode.OK

@workout_plans_ns.route(API.ADD_WORKOUT_TO_PLAN_ROUTE)
@workout_plans_ns.param('workout_plan_id', 'The workout plan identifier')
class AddWorkoutResource(Resource):
    """Endpoint for adding workouts to a plan"""

    @workout_plans_ns.doc('add_workout_to_plan')
    @workout_plans_ns.expect(add_workout_model)
    @workout_plans_ns.response(StatusCode.OK, Message.WORKOUT_ADDED_TO_PLAN, response_model)
    @workout_plans_ns.response(StatusCode.BAD_REQUEST, Message.MISSING_FIELDS)
    @workout_plans_ns.response(StatusCode.NOT_FOUND, Message.WORKOUT_PLAN_NOT_FOUND)
    @workout_plans_ns.response(StatusCode.UNAUTHORIZED, Message.UNAUTHORIZED_ROLE)
    @token_required
    @trainer_required
    def post(self, current_user, workout_plan_id):
        """
        Add a workout to a plan.

        Adds a workout to a workout plan with a specific order.
        Only the trainer who created the workout plan can add workouts to it.
        """
        data = request.get_json()

        if not data or not data.get(Database.WORKOUT_ID_KEY) or not data.get(Database.ORDER_KEY):
            return {'message': Message.MISSING_FIELDS}, StatusCode.BAD_REQUEST

        workout_plan = WorkoutPlan.query.get(workout_plan_id)
        if not workout_plan:
            return {'message': Message.WORKOUT_PLAN_NOT_FOUND}, StatusCode.NOT_FOUND

        if workout_plan.trainer_id != current_user.id:
            return {'message': Message.UNAUTHORIZED_ROLE}, StatusCode.UNAUTHORIZED

        workout = Workout.query.get(data.get(Database.WORKOUT_ID_KEY))
        if not workout:
            return {'message': Message.WORKOUT_NOT_FOUND}, StatusCode.NOT_FOUND

        # Add the workout to the plan with the specified order
        workout_plan.add_workout(workout, data.get(Database.ORDER_KEY))

        return {'message': Message.WORKOUT_ADDED_TO_PLAN, 'workout_plan': workout_plan.to_dict()}, StatusCode.OK

@workout_plans_ns.route(API.ASSIGN_PLAN_TO_GROUP_ROUTE)
@workout_plans_ns.param('workout_plan_id', 'The workout plan identifier')
class AssignPlanResource(Resource):
    """Endpoint for assigning workout plans to groups"""

    @workout_plans_ns.doc('assign_plan_to_group')
    @workout_plans_ns.expect(assign_plan_model)
    @workout_plans_ns.response(StatusCode.OK, Message.PLAN_ASSIGNED_TO_GROUP, response_model)
    @workout_plans_ns.response(StatusCode.BAD_REQUEST, Message.MISSING_FIELDS)
    @workout_plans_ns.response(StatusCode.NOT_FOUND, Message.WORKOUT_PLAN_NOT_FOUND)
    @workout_plans_ns.response(StatusCode.UNAUTHORIZED, Message.UNAUTHORIZED_ROLE)
    @token_required
    @trainer_required
    def post(self, current_user, workout_plan_id):
        """
        Assign a workout plan to a group.

        Assigns a workout plan to a group.
        Only the trainer who created the workout plan can assign it to a group.
        """
        data = request.get_json()

        if not data or not data.get(Database.GROUP_ID_KEY):
            return {'message': Message.MISSING_FIELDS}, StatusCode.BAD_REQUEST

        workout_plan = WorkoutPlan.query.get(workout_plan_id)
        if not workout_plan:
            return {'message': Message.WORKOUT_PLAN_NOT_FOUND}, StatusCode.NOT_FOUND

        if workout_plan.trainer_id != current_user.id:
            return {'message': Message.UNAUTHORIZED_ROLE}, StatusCode.UNAUTHORIZED

        group = Group.query.get(data.get(Database.GROUP_ID_KEY))
        if not group:
            return {'message': Message.GROUP_NOT_FOUND}, StatusCode.NOT_FOUND

        if group.trainer_id != current_user.id:
            return {'message': Message.UNAUTHORIZED_ROLE}, StatusCode.UNAUTHORIZED

        # Assign the workout plan to the group
        if group not in workout_plan.groups:
            workout_plan.groups.append(group)
            db.session.commit()

        return {'message': Message.PLAN_ASSIGNED_TO_GROUP, 'workout_plan': workout_plan.to_dict()}, StatusCode.OK

# Blueprint routes for backward compatibility
@workout_plans_bp.route(API.CREATE_WORKOUT_PLAN_ROUTE, methods=['POST'])
@token_required
@trainer_required
def create_workout_plan(current_user):
    """
    Create a new workout plan.

    Creates a new workout plan with the provided details.
    Only users with the Trainer role can create workout plans.

    Returns:
        201: Workout plan created successfully
        400: Missing required fields
        401: Unauthorized role
    """
    data = request.get_json()

    if not data or not data.get(Database.NAME_KEY):
        return jsonify({'message': Message.MISSING_FIELDS}), StatusCode.BAD_REQUEST

    new_workout_plan = WorkoutPlan(
        name=data.get(Database.NAME_KEY),
        description=data.get(Database.DESCRIPTION_KEY, ''),
        trainer_id=current_user.id
    )
    
    db.session.add(new_workout_plan)
    db.session.commit()

    return jsonify({'message': Message.WORKOUT_PLAN_CREATED, 'workout_plan': new_workout_plan.to_dict()}), StatusCode.CREATED

@workout_plans_bp.route(API.CREATE_WORKOUT_PLAN_ROUTE, methods=['GET'])
@token_required
def get_workout_plans(current_user):
    """
    Get all workout plans.

    Retrieves all workout plans. If the user is a trainer, only returns workout plans created by that trainer.
    If the user is a trainee, returns workout plans assigned to groups the trainee is a member of.

    Returns:
        200: Workout plans retrieved successfully
    """
    if current_user.role == UserRole.TRAINER:
        workout_plans = WorkoutPlan.query.filter_by(trainer_id=current_user.id).all()
    else:
        # For trainees, get workout plans assigned to their groups
        workout_plans = []
        for group in current_user.groups:
            workout_plans.extend(group.workout_plans)
        # Remove duplicates
        workout_plans = list(set(workout_plans))

    return jsonify({'workout_plans': [plan.to_dict() for plan in workout_plans]}), StatusCode.OK

@workout_plans_bp.route(API.GET_WORKOUT_PLAN_ROUTE, methods=['GET'])
@token_required
def get_workout_plan(current_user, workout_plan_id):
    """
    Get a specific workout plan.

    Retrieves the details of a specific workout plan.

    Returns:
        200: Workout plan retrieved successfully
        401: Unauthorized role
        404: Workout plan not found
    """
    workout_plan = WorkoutPlan.query.get(workout_plan_id)
    if not workout_plan:
        return jsonify({'message': Message.WORKOUT_PLAN_NOT_FOUND}), StatusCode.NOT_FOUND

    # Check if the user is authorized to view this workout plan
    if current_user.role == UserRole.TRAINER and workout_plan.trainer_id != current_user.id:
        return jsonify({'message': Message.UNAUTHORIZED_ROLE}), StatusCode.UNAUTHORIZED
    
    if current_user.role == UserRole.TRAINEE:
        # Check if the trainee is a member of any group assigned to this workout plan
        user_groups = set(current_user.groups)
        plan_groups = set(workout_plan.groups)
        if not user_groups.intersection(plan_groups):
            return jsonify({'message': Message.UNAUTHORIZED_ROLE}), StatusCode.UNAUTHORIZED

    return jsonify({'workout_plan': workout_plan.to_dict()}), StatusCode.OK

@workout_plans_bp.route(API.ADD_WORKOUT_TO_PLAN_ROUTE, methods=['POST'])
@token_required
@trainer_required
def add_workout_to_plan(current_user, workout_plan_id):
    """
    Add a workout to a plan.

    Adds a workout to a workout plan with a specific order.
    Only the trainer who created the workout plan can add workouts to it.

    Returns:
        200: Workout added to plan successfully
        400: Missing required fields
        401: Unauthorized role
        404: Workout plan or workout not found
    """
    data = request.get_json()

    if not data or not data.get(Database.WORKOUT_ID_KEY) or not data.get(Database.ORDER_KEY):
        return jsonify({'message': Message.MISSING_FIELDS}), StatusCode.BAD_REQUEST

    workout_plan = WorkoutPlan.query.get(workout_plan_id)
    if not workout_plan:
        return jsonify({'message': Message.WORKOUT_PLAN_NOT_FOUND}), StatusCode.NOT_FOUND

    if workout_plan.trainer_id != current_user.id:
        return jsonify({'message': Message.UNAUTHORIZED_ROLE}), StatusCode.UNAUTHORIZED

    workout = Workout.query.get(data.get(Database.WORKOUT_ID_KEY))
    if not workout:
        return jsonify({'message': Message.WORKOUT_NOT_FOUND}), StatusCode.NOT_FOUND

    # Add the workout to the plan with the specified order
    workout_plan.add_workout(workout, data.get(Database.ORDER_KEY))

    return jsonify({'message': Message.WORKOUT_ADDED_TO_PLAN, 'workout_plan': workout_plan.to_dict()}), StatusCode.OK

@workout_plans_bp.route(API.ASSIGN_PLAN_TO_GROUP_ROUTE, methods=['POST'])
@token_required
@trainer_required
def assign_plan_to_group(current_user, workout_plan_id):
    """
    Assign a workout plan to a group.

    Assigns a workout plan to a group.
    Only the trainer who created the workout plan can assign it to a group.

    Returns:
        200: Workout plan assigned to group successfully
        400: Missing required fields
        401: Unauthorized role
        404: Workout plan or group not found
    """
    data = request.get_json()

    if not data or not data.get(Database.GROUP_ID_KEY):
        return jsonify({'message': Message.MISSING_FIELDS}), StatusCode.BAD_REQUEST

    workout_plan = WorkoutPlan.query.get(workout_plan_id)
    if not workout_plan:
        return jsonify({'message': Message.WORKOUT_PLAN_NOT_FOUND}), StatusCode.NOT_FOUND

    if workout_plan.trainer_id != current_user.id:
        return jsonify({'message': Message.UNAUTHORIZED_ROLE}), StatusCode.UNAUTHORIZED

    group = Group.query.get(data.get(Database.GROUP_ID_KEY))
    if not group:
        return jsonify({'message': Message.GROUP_NOT_FOUND}), StatusCode.NOT_FOUND

    if group.trainer_id != current_user.id:
        return jsonify({'message': Message.UNAUTHORIZED_ROLE}), StatusCode.UNAUTHORIZED

    # Assign the workout plan to the group
    if group not in workout_plan.groups:
        workout_plan.groups.append(group)
        db.session.commit()

    return jsonify({'message': Message.PLAN_ASSIGNED_TO_GROUP, 'workout_plan': workout_plan.to_dict()}), StatusCode.OK
