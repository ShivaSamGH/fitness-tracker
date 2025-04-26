from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api, Resource
from models import db
from routes.auth import auth_bp, auth_ns
from routes.groups import groups_bp, groups_ns
from routes.workouts import workouts_bp, workouts_ns
from routes.workout_plans import workout_plans_bp, workout_plans_ns
from routes.progress import progress_bp, progress_ns
from config import Config
from constants import API, StatusCode, Message, AppConfig

def create_app(config_class=Config):
    """
    Create and configure the Flask application.

    Args:
        config_class: Configuration class for the application

    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Initialize Swagger documentation with flask-restx
    api = Api(
        app,
        version=API.VERSION,
        title=API.TITLE,
        description=API.DESCRIPTION,
        doc=API.DOCS_URL,
        prefix=API.PREFIX
    )

    # Add namespaces to the API
    api.add_namespace(auth_ns, path=API.AUTH_PATH)
    api.add_namespace(groups_ns, path=API.GROUPS_PATH)
    api.add_namespace(workouts_ns, path=API.WORKOUTS_PATH)
    api.add_namespace(workout_plans_ns, path=API.WORKOUT_PLANS_PATH)
    api.add_namespace(progress_ns, path=API.PROGRESS_PATH)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix=API.AUTH_URL_PREFIX)
    app.register_blueprint(groups_bp, url_prefix=API.GROUPS_URL_PREFIX)
    app.register_blueprint(workouts_bp, url_prefix=API.WORKOUTS_URL_PREFIX)
    app.register_blueprint(workout_plans_bp, url_prefix=API.WORKOUT_PLANS_URL_PREFIX)
    app.register_blueprint(progress_bp, url_prefix=API.PROGRESS_URL_PREFIX)

    # Create database tables
    with app.app_context():
        db.create_all()

    @app.route('/')
    def hello_world():
        """
        Root endpoint that returns a welcome message.

        Returns:
            str: Welcome message
        """
        return AppConfig.ROOT_MESSAGE

    @app.errorhandler(StatusCode.NOT_FOUND)
    def not_found(error):
        """
        Handle 404 errors.

        Args:
            error: The error object

        Returns:
            tuple: JSON response with error message and 404 status code
        """
        return jsonify({'message': Message.RESOURCE_NOT_FOUND}), StatusCode.NOT_FOUND

    @app.errorhandler(StatusCode.INTERNAL_SERVER_ERROR)
    def internal_error(error):
        """
        Handle 500 errors.

        Args:
            error: The error object

        Returns:
            tuple: JSON response with error message and 500 status code
        """
        return jsonify({'message': Message.INTERNAL_SERVER_ERROR}), StatusCode.INTERNAL_SERVER_ERROR

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=AppConfig.DEBUG)
