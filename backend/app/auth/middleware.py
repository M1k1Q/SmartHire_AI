"""
auth/middleware.py — JWT-based auth decorators for role-based access control.

Usage:
    @require_auth          — Any authenticated user
    @require_role('hr')    — HR/Admin only
    @require_role('candidate') — Candidate only
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity


def require_auth(fn):
    """Decorator: requires a valid JWT token."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            from flask import request, current_app
            # Debug: Log incoming headers (masked)
            auth_header = request.headers.get("Authorization", "")
            current_app.logger.debug(f"Auth Header: {auth_header[:15]}..." if auth_header else "Missing Auth Header")
            
            verify_jwt_in_request()
        except Exception as e:
            from flask import current_app
            current_app.logger.warning(f"Auth failed: {e}")
            return jsonify({"error": "Authentication required.", "details": str(e)}), 401
        return fn(*args, **kwargs)
    return wrapper


def require_role(*roles):
    """
    Decorator factory: requires the authenticated user to have one of the specified roles.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                from flask import request, current_app
                from flask_jwt_extended import get_jwt
                
                # Debug: Log incoming headers
                auth_header = request.headers.get("Authorization", "")
                if not auth_header:
                    current_app.logger.error(f"Missing Authorization Header for {request.path}")
                
                verify_jwt_in_request()
                claims = get_jwt()
                user_role = claims.get("role", "")

                if user_role not in roles:
                    current_app.logger.warning(f"Role mismatch for {request.path}: user has '{user_role}', needs {roles}")
                    return jsonify({
                        "error": "Access denied.",
                        "details": f"Required role(s): {', '.join(roles)}. You have: {user_role}"
                    }), 403
            except Exception as e:
                from flask import current_app
                current_app.logger.error(f"require_role failed for {request.path}: {e}")
                return jsonify({"error": "Authentication required.", "details": str(e)}), 401
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user_id() -> str:
    """Helper to extract the current user's ID from JWT identity."""
    return get_jwt_identity()


def get_current_role() -> str:
    """Helper to extract the current user's role from JWT custom claims."""
    from flask_jwt_extended import get_jwt
    return get_jwt().get("role", "")
