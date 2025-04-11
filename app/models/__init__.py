from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_app(app):
    db.init_app(app)
    
    # Import models here to avoid circular imports
    from app.models.user import User
    from app.models.backup import Backup
    from app.models.db_credential import DBCredential
    
    with app.app_context():
        db.create_all() 