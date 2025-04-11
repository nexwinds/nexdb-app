from datetime import datetime
from app.models import db

class DBCredential(db.Model):
    __tablename__ = 'db_credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    db_type = db.Column(db.String(20), nullable=False)  # mysql or postgres
    username = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    host = db.Column(db.String(120), default='localhost')
    port = db.Column(db.Integer)  # 3306 for MySQL, 5432 for PostgreSQL
    database = db.Column(db.String(64), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, db_type, username, password, host='localhost', port=None, database=None, created_by=None):
        self.db_type = db_type
        self.username = username
        self.password = password
        self.host = host
        
        # Set default port based on DB type if not provided
        if port is None:
            self.port = 3306 if db_type == 'mysql' else 5432
        else:
            self.port = port
            
        self.database = database
        self.created_by = created_by
    
    def to_dict(self):
        return {
            'id': self.id,
            'db_type': self.db_type,
            'username': self.username,
            'password': self.password,
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 