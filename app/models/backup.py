from datetime import datetime
from app.models import db

class Backup(db.Model):
    __tablename__ = 'backups'
    
    id = db.Column(db.Integer, primary_key=True)
    db_type = db.Column(db.String(20), nullable=False)  # mysql or postgres
    db_name = db.Column(db.String(64), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, default=0)  # Size in bytes
    status = db.Column(db.String(20), default='completed')  # completed, failed, in_progress
    s3_uploaded = db.Column(db.Boolean, default=False)
    s3_path = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, db_type, db_name, file_path, created_by=None, file_size=0):
        self.db_type = db_type
        self.db_name = db_name
        self.file_path = file_path
        self.created_by = created_by
        self.file_size = file_size
    
    def to_dict(self):
        return {
            'id': self.id,
            'db_type': self.db_type,
            'db_name': self.db_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'status': self.status,
            's3_uploaded': self.s3_uploaded,
            's3_path': self.s3_path,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        } 