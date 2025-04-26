"""
Utility functions for the Fitness Tracker application.

This file contains utility functions and decorators used throughout the application.
"""

from functools import wraps
from flask import jsonify
from constants import StatusCode, Message, UserRole

def role_required(allowed_roles):
    """
    Decorator to restrict access to endpoints based on user roles.
    
    Args:
        allowed_roles (list): List of roles allowed to access the endpoint
        
    Returns:
        function: Decorated function that checks if the user has the required role
        
    Raises:
        401: If user role is not in the allowed roles
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(self_instance, current_user, *args, **kwargs):
            if current_user.role not in allowed_roles:
                return jsonify({'message': Message.UNAUTHORIZED_ROLE}), StatusCode.UNAUTHORIZED
            return f(self_instance, current_user, *args, **kwargs)
        return decorated_function
    return decorator

def trainer_required(f):
    """
    Decorator to restrict access to endpoints to users with the Trainer role.
    
    Args:
        f: The function to decorate
        
    Returns:
        function: Decorated function that checks if the user has the Trainer role
    """
    return role_required([UserRole.TRAINER])(f)

def trainee_required(f):
    """
    Decorator to restrict access to endpoints to users with the Trainee role.
    
    Args:
        f: The function to decorate
        
    Returns:
        function: Decorated function that checks if the user has the Trainee role
    """
    return role_required([UserRole.TRAINEE])(f)

def generate_invite_code():
    """
    Generate a random invite code for group invitations.
    
    Returns:
        str: A random string to be used as an invite code
    """
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
