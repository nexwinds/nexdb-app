from flask_sqlalchemy import SQLAlchemy

# Create an empty SQLAlchemy instance
db = SQLAlchemy()

def init_app(app):
    """Initialize the SQLAlchemy instance with the Flask app"""
    db.init_app(app)
    
    # Create all tables if they don't exist
    with app.app_context():
        try:
            # Import models
            from app.models.user import User
            from app.models.db_credential import DBCredential
            from app.models.backup import Backup
            from app.models.backup_schedule import BackupSchedule
            
            # Create tables
            db.create_all()
        except Exception as e:
            # Log the error but don't crash the app
            print(f"Error initializing database: {str(e)}")
            
            # Create a minimal fallback model structure
            class User(db.Model):
                id = db.Column(db.Integer, primary_key=True)
                username = db.Column(db.String(50), unique=True, nullable=False)
                email = db.Column(db.String(100), unique=True, nullable=False)
                password_hash = db.Column(db.String(256), nullable=False)
                is_admin = db.Column(db.Boolean, default=False)
                
            class DBCredential(db.Model):
                id = db.Column(db.Integer, primary_key=True)
                db_name = db.Column(db.String(100), nullable=False)
                db_type = db.Column(db.String(20), nullable=False)
                username = db.Column(db.String(50), nullable=False)
                password = db.Column(db.String(100), nullable=False)
                
            class Backup(db.Model):
                id = db.Column(db.Integer, primary_key=True)
                db_name = db.Column(db.String(100), nullable=False)
                db_type = db.Column(db.String(20), nullable=False)
                file_path = db.Column(db.String(255), nullable=False)
                
            class BackupSchedule(db.Model):
                id = db.Column(db.Integer, primary_key=True)
                db_name = db.Column(db.String(100), nullable=False)
                db_type = db.Column(db.String(20), nullable=False)
                frequency = db.Column(db.String(20), nullable=False)
            
            # Create these fallback tables
            db.create_all()
            
    return db 