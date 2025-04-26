from flask import Blueprint, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from models.user import User, db
from config import Config
from functools import wraps
from flask_restx import Namespace, Resource, fields
from constants import StatusCode, Message, API, JWT, HttpMethod, Database, USERNAME_KEY, PASSWORD_KEY, ROLE_KEY

auth_bp = Blueprint('auth', __name__)

# Create a namespace for authentication routes
auth_ns = Namespace('auth', description='Authentication operations')

# Define models for request and response payloads
user_model = auth_ns.model('User', {
    Database.ID_KEY: fields.Integer(readonly=True, description='The user identifier'),
    USERNAME_KEY: fields.String(required=True, description='The user username'),
    ROLE_KEY: fields.String(required=True, description='The user role'),
    Database.CREATED_AT_KEY: fields.DateTime(readonly=True, description='Timestamp when the user was created')
})

signup_model = auth_ns.model('SignupRequest', {
    USERNAME_KEY: fields.String(required=True, description='The user username'),
    PASSWORD_KEY: fields.String(required=True, description='The user password'),
    ROLE_KEY: fields.String(required=True, description='The user role', enum=Config.ALLOWED_ROLES)
})

signin_model = auth_ns.model('SigninRequest', {
    USERNAME_KEY: fields.String(required=True, description='The user username'),
    PASSWORD_KEY: fields.String(required=True, description='The user password')
})

response_model = auth_ns.model('Response', {
    'message': fields.String(required=True, description='Response message'),
    'user': fields.Nested(user_model, description='User information')
})

@auth_ns.route(API.SIGNUP_ROUTE)
class SignupResource(Resource):
    """Endpoint for user registration"""

    @auth_ns.doc('create_user')
    @auth_ns.expect(signup_model)
    @auth_ns.response(StatusCode.CREATED, Message.USER_CREATED, response_model)
    @auth_ns.response(StatusCode.BAD_REQUEST, Message.MISSING_FIELDS)
    @auth_ns.response(StatusCode.CONFLICT, Message.USERNAME_EXISTS)
    def post(self):
        """
        Register a new user.

        Creates a new user with the provided username, password, and role.
        """
        data = request.get_json()

        if not data or not data.get(USERNAME_KEY) or not data.get(PASSWORD_KEY) or not data.get(ROLE_KEY):
            return {'message': Message.MISSING_FIELDS}, StatusCode.BAD_REQUEST

        if data.get(ROLE_KEY) not in Config.ALLOWED_ROLES:
            return {'message': Message.INVALID_ROLE_FORMAT.format(", ".join(Config.ALLOWED_ROLES))}, StatusCode.BAD_REQUEST

        existing_user = User.query.filter_by(username=data.get(USERNAME_KEY)).first()
        if existing_user:
            return {'message': Message.USERNAME_EXISTS}, StatusCode.CONFLICT

        new_user = User(
            username=data.get(USERNAME_KEY),
            password=data.get(PASSWORD_KEY),
            role=data.get(ROLE_KEY)
        )
        db.session.add(new_user)
        db.session.commit()

        return {'message': Message.USER_CREATED, 'user': new_user.to_dict()}, StatusCode.CREATED

@auth_ns.route(API.SIGNIN_ROUTE)
class SigninResource(Resource):
    """Endpoint for user authentication"""

    @auth_ns.doc('login_user')
    @auth_ns.expect(signin_model)
    @auth_ns.response(StatusCode.OK, Message.LOGIN_SUCCESSFUL, response_model)
    @auth_ns.response(StatusCode.BAD_REQUEST, Message.MISSING_FIELDS)
    @auth_ns.response(StatusCode.UNAUTHORIZED, Message.INVALID_CREDENTIALS)
    def post(self):
        """
        Authenticate a user and issue a JWT token.

        Validates the username and password and returns a JWT token as a cookie.
        """
        data = request.get_json()

        if not data or not data.get(USERNAME_KEY) or not data.get(PASSWORD_KEY):
            return {'message': Message.MISSING_FIELDS}, StatusCode.BAD_REQUEST

        user = User.query.filter_by(username=data.get(USERNAME_KEY)).first()

        if not user or not user.check_password(data.get(PASSWORD_KEY)):
            return {'message': Message.INVALID_CREDENTIALS}, StatusCode.UNAUTHORIZED

        token = jwt.encode({
            JWT.USER_ID_FIELD: user.id,
            JWT.USERNAME_FIELD: user.username,
            JWT.ROLE_FIELD: user.role,
            JWT.EXPIRATION_FIELD: datetime.datetime.now(datetime.UTC) + Config.JWT_ACCESS_TOKEN_EXPIRES
        }, Config.JWT_SECRET_KEY)
        response = make_response({'message': Message.LOGIN_SUCCESSFUL, 'user': user.to_dict()})
        response.set_cookie(JWT.COOKIE_NAME, token, httponly=True, max_age=int(Config.JWT_ACCESS_TOKEN_EXPIRES.total_seconds()))

        return response

def token_required(f):
    """
    Decorator to protect routes that require authentication.

    Verifies the JWT token from cookies and passes the current user to the check_auth function.

    Args:
        f: The function to decorate

    Returns:
        check_auth: The check_auth function that checks for a valid token

    Raises:
        401: If token is missing or invalid
    """
    @wraps(f)
    def check_auth(*args, **kwargs):
        self_instance = args[0]
        other_args = args[1:]
        token = request.cookies.get(JWT.COOKIE_NAME)

        if not token:
            return jsonify({'message': Message.TOKEN_MISSING}), StatusCode.UNAUTHORIZED

        try:
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[JWT.ALGORITHM])
            current_user = User.query.filter_by(id=data[JWT.USER_ID_FIELD]).first()
        except:
            return jsonify({'message': Message.TOKEN_INVALID}), StatusCode.UNAUTHORIZED

        return f(self_instance, current_user, *other_args, **kwargs)

    return check_auth

# Blueprint routes for backward compatibility
@auth_bp.route(API.SIGNUP_ROUTE, methods=[HttpMethod.POST])
def signup():
    """
    Register a new user.

    Expects a JSON payload with username, password, and role.

    Returns:
        201: User created successfully
        400: Missing required fields or invalid role
        409: Username already exists
    """
    data = request.get_json()

    if not data or not data.get(USERNAME_KEY) or not data.get(PASSWORD_KEY) or not data.get(ROLE_KEY):
        return jsonify({'message': Message.MISSING_FIELDS}), StatusCode.BAD_REQUEST

    if data.get(ROLE_KEY) not in Config.ALLOWED_ROLES:
        return jsonify({'message': Message.INVALID_ROLE_FORMAT.format(", ".join(Config.ALLOWED_ROLES))}), StatusCode.BAD_REQUEST

    existing_user = User.query.filter_by(username=data.get(USERNAME_KEY)).first()
    if existing_user:
        return jsonify({'message': Message.USERNAME_EXISTS}), StatusCode.CONFLICT

    new_user = User(
        username=data.get(USERNAME_KEY),
        password=data.get(PASSWORD_KEY),
        role=data.get(ROLE_KEY)
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': Message.USER_CREATED, 'user': new_user.to_dict()}), StatusCode.CREATED

@auth_bp.route(API.SIGNIN_ROUTE, methods=[HttpMethod.POST])
def signin():
    """
    Authenticate a user and issue a JWT token.

    Expects a JSON payload with username and password.

    Returns:
        200: Login successful, sets JWT cookie
        400: Missing required fields
        401: Invalid username or password
    """
    data = request.get_json()

    if not data or not data.get(USERNAME_KEY) or not data.get(PASSWORD_KEY):
        return jsonify({'message': Message.MISSING_FIELDS}), StatusCode.BAD_REQUEST

    user = User.query.filter_by(username=data.get(USERNAME_KEY)).first()

    if not user or not user.check_password(data.get(PASSWORD_KEY)):
        return jsonify({'message': Message.INVALID_CREDENTIALS}), StatusCode.UNAUTHORIZED

    token = jwt.encode({
        JWT.USER_ID_FIELD: user.id,
        JWT.USERNAME_FIELD: user.username,
        JWT.ROLE_FIELD: user.role,
        JWT.EXPIRATION_FIELD: datetime.datetime.now(datetime.UTC) + Config.JWT_ACCESS_TOKEN_EXPIRES
    }, Config.JWT_SECRET_KEY)
    response = make_response(jsonify({'message': Message.LOGIN_SUCCESSFUL, 'user': user.to_dict()}))
    response.set_cookie(JWT.COOKIE_NAME, token, httponly=True, max_age=int(Config.JWT_ACCESS_TOKEN_EXPIRES.total_seconds()))

    return response
