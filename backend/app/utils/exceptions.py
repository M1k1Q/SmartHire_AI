"""
exceptions.py — Custom exception classes and global Flask error handlers.
"""
from flask import jsonify


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when input validation fails."""
    status_code = 400

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code:
            self.status_code = status_code


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    status_code = 401

    def __init__(self, message="Authentication required"):
        super().__init__(message)
        self.message = message


class AuthorizationError(Exception):
    """Raised when the user lacks permission."""
    status_code = 403

    def __init__(self, message="Insufficient permissions"):
        super().__init__(message)
        self.message = message


class NotFoundError(Exception):
    """Raised when a resource is not found."""
    status_code = 404

    def __init__(self, message="Resource not found"):
        super().__init__(message)
        self.message = message


class MLPipelineError(Exception):
    """Raised when the ML pipeline encounters an error."""
    status_code = 500

    def __init__(self, message="ML pipeline error"):
        super().__init__(message)
        self.message = message


# ---------------------------------------------------------------------------
# Flask Error Handler Registration
# ---------------------------------------------------------------------------

def register_error_handlers(app):
    """Register global error handlers on the Flask app."""

    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify({"error": e.message, "type": "ValidationError"}), e.status_code

    @app.errorhandler(AuthenticationError)
    def handle_auth_error(e):
        return jsonify({"error": e.message, "type": "AuthenticationError"}), e.status_code

    @app.errorhandler(AuthorizationError)
    def handle_authz_error(e):
        return jsonify({"error": e.message, "type": "AuthorizationError"}), e.status_code

    @app.errorhandler(NotFoundError)
    def handle_not_found(e):
        return jsonify({"error": e.message, "type": "NotFoundError"}), e.status_code

    @app.errorhandler(MLPipelineError)
    def handle_ml_error(e):
        return jsonify({"error": e.message, "type": "MLPipelineError"}), e.status_code

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f"Internal server error: {e}")
        return jsonify({"error": "Internal server error"}), 500
