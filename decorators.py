from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def check_roles(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in allowed_roles:
                return jsonify(error="You do not have permission to perform this action."), 403
            if claims.get("status") in ("Blacklisted",):
                return jsonify(error="This account has been blacklisted."), 403
            return view_func(*args, **kwargs)
        return wrapped
    return decorator
