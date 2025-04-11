from flask import Blueprint

# Create route blueprints
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
backup_bp = Blueprint('backup', __name__, url_prefix='/backup')
database_bp = Blueprint('database', __name__, url_prefix='/database')
user_bp = Blueprint('user', __name__, url_prefix='/user')
settings_bp = Blueprint('settings', __name__, url_prefix='/settings')
api_bp = Blueprint('api', __name__, url_prefix='/api')
projects_bp = Blueprint('projects', __name__, url_prefix='/projects')

# Import routes
from app.routes.auth import *
from app.routes.dashboard import *
from app.routes.backup import *
from app.routes.database import *
from app.routes.user import *
from app.routes.settings import *
from app.routes.api import *
from app.routes.projects import *

def register_blueprints(app):
    """Register all blueprints with the Flask application"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(backup_bp)
    app.register_blueprint(database_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(projects_bp) 