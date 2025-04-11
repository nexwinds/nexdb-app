from flask import Flask, redirect, url_for, jsonify
from config import SECRET_KEY, HOST, PORT, ADMIN_USER, ADMIN_PASS
import os

def create_app():
    """Initialize the Flask application"""
    # Create Flask app
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nexdb.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    from app.models import init_app as init_db
    init_db(app)
    
    # Register routes
    from app.routes import register_blueprints
    register_blueprints(app)
    
    # Create default admin user
    with app.app_context():
        from app.services.user_service import UserService
        admin, password = UserService.initialize_admin_user(
            username=ADMIN_USER,
            email="admin@local.nexdb",
            password=ADMIN_PASS
        )
        
        if password:
            app.config['ADMIN_PASSWORD'] = password
    
    # Root route
    @app.route('/')
    def index():
        return redirect(url_for('dashboard.index'))
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'ok',
            'version': app.config.get('VERSION', '1.0.0'),
            'host': HOST,
            'port': PORT
        })
    
    return app

def run_app():
    """Run the application"""
    app = create_app()
    print(f"Starting NEXDB on {HOST}:{PORT}...")
    app.run(host=HOST, port=PORT, debug=False)
    
if __name__ == '__main__':
    run_app() 