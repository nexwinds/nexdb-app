"""
NEXDB - Backup model
"""

from datetime import datetime
import json
from app import db

class Backup(db.Model):
    """Backup model for database backups."""
    __tablename__ = 'backups'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    size_bytes = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    location = db.Column(db.String(20), default='local')  # local, s3
    s3_path = db.Column(db.String(255))
    database_id = db.Column(db.Integer, db.ForeignKey('databases.id'), nullable=False)
    metadata = db.Column(db.Text)  # JSON-encoded metadata
    
    @property
    def metadata_dict(self):
        """Return metadata as a dictionary."""
        if not self.metadata:
            return {}
        return json.loads(self.metadata)
    
    @metadata_dict.setter
    def metadata_dict(self, metadata_dict):
        """Store metadata dictionary as JSON."""
        self.metadata = json.dumps(metadata_dict)
    
    def __repr__(self):
        return f'<Backup {self.filename}>'


class BackupSchedule(db.Model):
    """BackupSchedule model for scheduled database backups."""
    __tablename__ = 'backup_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    database_id = db.Column(db.Integer, db.ForeignKey('databases.id'), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly
    time = db.Column(db.Time, nullable=False)  # Time of day to run backup
    day_of_week = db.Column(db.Integer)  # 0=Monday, 6=Sunday (for weekly backups)
    day_of_month = db.Column(db.Integer)  # 1-31 (for monthly backups)
    retention_count = db.Column(db.Integer, default=7)  # Number of backups to keep
    enabled = db.Column(db.Boolean, default=True)
    upload_to_s3 = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    database = db.relationship('Database', backref='backup_schedules')
    
    def get_next_run_time(self):
        """Calculate the next run time based on the schedule."""
        # This would normally use APScheduler's utilities to calculate the next run time
        # For simplicity, we'll leave the implementation details out
        pass
    
    def __repr__(self):
        return f'<BackupSchedule {self.frequency} for Database ID {self.database_id}>' 