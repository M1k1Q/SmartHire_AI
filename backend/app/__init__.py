"""
__init__.py — Flask application factory for Smart Recruitment Platform.
"""
import os
from flask import Flask, jsonify
from .config import get_config
from .extensions import mongo, jwt, cors, bcrypt
from .utils.logger import setup_logger
from .utils.exceptions import register_error_handlers


def create_app(config_class=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load config
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Ensure required directories exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["MODELS_FOLDER"], exist_ok=True)

    # Initialize extensions
    mongo.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, 
        origins=app.config["CORS_ORIGINS"], 
        supports_credentials=True,
        allow_headers=["Authorization", "Content-Type"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    # Setup logging
    setup_logger(app)

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    from .auth.routes import auth_bp
    from .routes.jobs import jobs_bp
    from .routes.applications import applications_bp
    from .routes.analytics import analytics_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(jobs_bp, url_prefix="/api/jobs")
    app.register_blueprint(applications_bp, url_prefix="/api/applications")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    # Health check
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "Smart Recruitment API"}), 200

    return app
