"""
NEXDB - A Modern Web-Based Database Control Panel
Main application initialization
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_cors import CORS
from flask_apscheduler import APScheduler

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
jwt = JWTManager()
csrf = CSRFProtect()
bcrypt = Bcrypt()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
scheduler = APScheduler()

def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    from config.config import config_by_name
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    scheduler.init_app(app)
    scheduler.start()
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Security headers with Talisman
    csp = {
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'"],  # Consider tightening in production
        'style-src': ["'self'", "'unsafe-inline'"],
        'img-src': ["'self'", 'data:'],
        'font-src': ["'self'"],
    }
    Talisman(app, content_security_policy=csp, force_https=False)  # Set to True in production
    
    # Enable CORS for API routes only
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register blueprints
    from app.auth.routes import auth_bp
    from app.api.routes import api_bp
    from app.database.routes import database_bp
    from app.backup.routes import backup_bp
    from app.project.routes import project_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(database_bp, url_prefix='/database')
    app.register_blueprint(backup_bp, url_prefix='/backup')
    app.register_blueprint(project_bp, url_prefix='/project')
    
    # Register error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)
    
    # Register CLI commands
    from app.cli import register_cli_commands
    register_cli_commands(app)
    
    # Create all database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    return app 