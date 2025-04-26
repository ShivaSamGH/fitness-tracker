"""
Group management routes for the Fitness Tracker application.

This file contains routes for creating and managing groups.
"""

from flask import Blueprint, request, jsonify
from flask_restx import Namespace, Resource, fields
from models import db, Group, User
from routes.auth import token_required
from utils import trainer_required, trainee_required, generate_invite_code
from constants import StatusCode, Message, API, Database, UserRole

groups_bp = Blueprint('groups', __name__)

# Create a namespace for group routes
groups_ns = Namespace('groups', description='Group operations')

# Define models for request and response payloads
group_model = groups_ns.model('Group', {
    Database.ID_KEY: fields.Integer(readonly=True, description='The group identifier'),
    Database.NAME_KEY: fields.String(required=True, description='The group name'),
    Database.DESCRIPTION_KEY: fields.String(description='The group description'),
    'trainer_id': fields.Integer(readonly=True, description='The trainer identifier'),
    Database.INVITE_CODE_KEY: fields.String(readonly=True, description='The group invite code'),
    Database.CREATED_AT_KEY: fields.DateTime(readonly=True, description='Timestamp when the group was created'),
    'members_count': fields.Integer(readonly=True, description='Number of members in the group')
})

create_group_model = groups_ns.model('CreateGroupRequest', {
    Database.NAME_KEY: fields.String(required=True, description='The group name'),
    Database.DESCRIPTION_KEY: fields.String(description='The group description')
})

join_group_model = groups_ns.model('JoinGroupRequest', {
    Database.INVITE_CODE_KEY: fields.String(required=True, description='The group invite code')
})

user_model = groups_ns.model('User', {
    Database.ID_KEY: fields.Integer(readonly=True, description='The user identifier'),
    Database.USERNAME_KEY: fields.String(readonly=True, description='The user username'),
    Database.ROLE_KEY: fields.String(readonly=True, description='The user role'),
    Database.CREATED_AT_KEY: fields.DateTime(readonly=True, description='Timestamp when the user was created')
})

members_model = groups_ns.model('GroupMembers', {
    'members': fields.List(fields.Nested(user_model), description='List of group members')
})

response_model = groups_ns.model('Response', {
    'message': fields.String(required=True, description='Response message'),
    'group': fields.Nested(group_model, description='Group information')
})

invite_response_model = groups_ns.model('InviteResponse', {
    'message': fields.String(required=True, description='Response message'),
    Database.INVITE_CODE_KEY: fields.String(required=True, description='The group invite code')
})

@groups_ns.route(API.CREATE_GROUP_ROUTE)
class GroupResource(Resource):
    """Endpoint for group management"""

    @groups_ns.doc('create_group')
    @groups_ns.expect(create_group_model)
    @groups_ns.response(StatusCode.CREATED, Message.GROUP_CREATED, response_model)
    @groups_ns.response(StatusCode.BAD_REQUEST, Message.MISSING_FIELDS)
    @groups_ns.response(StatusCode.UNAUTHORIZED, Message.UNAUTHORIZED_ROLE)
    @token_required
    @trainer_required
    def post(self, current_user, *args, **kwargs):
        """
        Create a new group.

        Creates a new group with the provided name and description.
        Only users with the Trainer role can create groups.
        """
        data = request.get_json()

        if not data or not data.get(Database.NAME_KEY):
            return {'message': Message.MISSING_FIELDS}, StatusCode.BAD_REQUEST

        invite_code = generate_invite_code()
        new_group = Group(
            name=data.get(Database.NAME_KEY),
            description=data.get(Database.DESCRIPTION_KEY, ''),
            trainer_id=current_user.id,
            invite_code=invite_code
        )
        
        # Add the trainer as a member of the group
        new_group.members.append(current_user)
        
        db.session.add(new_group)
        db.session.commit()

        return {'message': Message.GROUP_CREATED, 'group': new_group.to_dict()}, StatusCode.CREATED

@groups_ns.route(API.JOIN_GROUP_ROUTE)
class JoinGroupResource(Resource):
    """Endpoint for joining a group"""

    @groups_ns.doc('join_group')
    @groups_ns.expect(join_group_model)
    @groups_ns.response(StatusCode.OK, Message.JOINED_GROUP, response_model)
    @groups_ns.response(StatusCode.BAD_REQUEST, Message.MISSING_FIELDS)
    @groups_ns.response(StatusCode.NOT_FOUND, Message.GROUP_NOT_FOUND)
    @groups_ns.response(StatusCode.CONFLICT, Message.ALREADY_MEMBER)
    @token_required
    @trainee_required
    def post(self, current_user):
        """
        Join a group using an invite code.

        Allows a trainee to join a group using the invite code.
        Only users with the Trainee role can join groups.
        """
        data = request.get_json()

        if not data or not data.get(Database.INVITE_CODE_KEY):
            return {'message': Message.MISSING_FIELDS}, StatusCode.BAD_REQUEST

        group = Group.query.filter_by(invite_code=data.get(Database.INVITE_CODE_KEY)).first()
        if not group:
            return {'message': Message.GROUP_NOT_FOUND}, StatusCode.NOT_FOUND

        if current_user in group.members:
            return {'message': Message.ALREADY_MEMBER}, StatusCode.CONFLICT

        group.members.append(current_user)
        db.session.commit()

        return {'message': Message.JOINED_GROUP, 'group': group.to_dict()}, StatusCode.OK

@groups_ns.route(API.GROUP_INVITE_ROUTE)
@groups_ns.param('group_id', 'The group identifier')
class GroupInviteResource(Resource):
    """Endpoint for generating group invite codes"""

    @groups_ns.doc('generate_invite')
    @groups_ns.response(StatusCode.OK, 'Invite code generated', invite_response_model)
    @groups_ns.response(StatusCode.NOT_FOUND, Message.GROUP_NOT_FOUND)
    @groups_ns.response(StatusCode.UNAUTHORIZED, Message.UNAUTHORIZED_ROLE)
    @token_required
    @trainer_required
    def post(self, current_user, group_id):
        """
        Generate a new invite code for a group.

        Generates a new invite code for the specified group.
        Only the trainer who created the group can generate invite codes.
        """
        group = Group.query.get(group_id)
        if not group:
            return {'message': Message.GROUP_NOT_FOUND}, StatusCode.NOT_FOUND

        if group.trainer_id != current_user.id:
            return {'message': Message.UNAUTHORIZED_ROLE}, StatusCode.UNAUTHORIZED

        # Generate a new invite code
        group.invite_code = generate_invite_code()
        db.session.commit()

        return {
            Database.INVITE_CODE_KEY: group.invite_code
        }, StatusCode.OK

@groups_ns.route(API.GROUP_MEMBERS_ROUTE)
@groups_ns.param('group_id', 'The group identifier')
class GroupMembersResource(Resource):
    """Endpoint for viewing group members"""

    @groups_ns.doc('get_members')
    @groups_ns.response(StatusCode.OK, 'Group members retrieved', members_model)
    @groups_ns.response(StatusCode.NOT_FOUND, Message.GROUP_NOT_FOUND)
    @groups_ns.response(StatusCode.UNAUTHORIZED, Message.UNAUTHORIZED_ROLE)
    @token_required
    def get(self, current_user, group_id):
        """
        Get the members of a group.

        Retrieves the list of members in the specified group.
        Users can only view members of groups they belong to.
        """
        group = Group.query.get(group_id)
        if not group:
            return {'message': Message.GROUP_NOT_FOUND}, StatusCode.NOT_FOUND

        # Check if the user is a member of the group or the trainer
        if current_user not in group.members and current_user.id != group.trainer_id:
            return {'message': Message.UNAUTHORIZED_ROLE}, StatusCode.UNAUTHORIZED

        return {
            'members': [member.to_dict() for member in group.members]
        }, StatusCode.OK

# Blueprint routes for backward compatibility
@groups_bp.route(API.CREATE_GROUP_ROUTE, methods=['POST'])
@token_required
@trainer_required
def create_group(current_user):
    """
    Create a new group.

    Creates a new group with the provided name and description.
    Only users with the Trainer role can create groups.

    Returns:
        201: Group created successfully
        400: Missing required fields
        401: Unauthorized role
    """
    data = request.get_json()

    if not data or not data.get(Database.NAME_KEY):
        return jsonify({'message': Message.MISSING_FIELDS}), StatusCode.BAD_REQUEST

    invite_code = generate_invite_code()
    new_group = Group(
        name=data.get(Database.NAME_KEY),
        description=data.get(Database.DESCRIPTION_KEY, ''),
        trainer_id=current_user.id,
        invite_code=invite_code
    )
    
    # Add the trainer as a member of the group
    new_group.members.append(current_user)
    
    db.session.add(new_group)
    db.session.commit()

    return jsonify({'message': Message.GROUP_CREATED, 'group': new_group.to_dict()}), StatusCode.CREATED

@groups_bp.route(API.JOIN_GROUP_ROUTE, methods=['POST'])
@token_required
@trainee_required
def join_group(current_user):
    """
    Join a group using an invite code.

    Allows a trainee to join a group using the invite code.
    Only users with the Trainee role can join groups.

    Returns:
        200: Joined group successfully
        400: Missing required fields
        401: Unauthorized role
        404: Group not found
        409: Already a member of the group
    """
    data = request.get_json()

    if not data or not data.get(Database.INVITE_CODE_KEY):
        return jsonify({'message': Message.MISSING_FIELDS}), StatusCode.BAD_REQUEST

    group = Group.query.filter_by(invite_code=data.get(Database.INVITE_CODE_KEY)).first()
    if not group:
        return jsonify({'message': Message.GROUP_NOT_FOUND}), StatusCode.NOT_FOUND

    if current_user in group.members:
        return jsonify({'message': Message.ALREADY_MEMBER}), StatusCode.CONFLICT

    group.members.append(current_user)
    db.session.commit()

    return jsonify({'message': Message.JOINED_GROUP, 'group': group.to_dict()}), StatusCode.OK

@groups_bp.route(API.GROUP_INVITE_ROUTE, methods=['POST'])
@token_required
@trainer_required
def generate_invite(current_user, group_id):
    """
    Generate a new invite code for a group.

    Generates a new invite code for the specified group.
    Only the trainer who created the group can generate invite codes.

    Returns:
        200: Invite code generated successfully
        401: Unauthorized role
        404: Group not found
    """
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'message': Message.GROUP_NOT_FOUND}), StatusCode.NOT_FOUND

    if group.trainer_id != current_user.id:
        return jsonify({'message': Message.UNAUTHORIZED_ROLE}), StatusCode.UNAUTHORIZED

    # Generate a new invite code
    group.invite_code = generate_invite_code()
    db.session.commit()

    return jsonify({
        'message': Message.INVITE_CREATED,
        Database.INVITE_CODE_KEY: group.invite_code
    }), StatusCode.OK

@groups_bp.route(API.GROUP_MEMBERS_ROUTE, methods=['GET'])
@token_required
def get_members(current_user, group_id):
    """
    Get the members of a group.

    Retrieves the list of members in the specified group.
    Users can only view members of groups they belong to.

    Returns:
        200: Group members retrieved successfully
        401: Unauthorized role
        404: Group not found
    """
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'message': Message.GROUP_NOT_FOUND}), StatusCode.NOT_FOUND

    # Check if the user is a member of the group or the trainer
    if current_user not in group.members and current_user.id != group.trainer_id:
        return jsonify({'message': Message.UNAUTHORIZED_ROLE}), StatusCode.UNAUTHORIZED

    return jsonify({
        'members': [member.to_dict() for member in group.members]
    }), StatusCode.OK
