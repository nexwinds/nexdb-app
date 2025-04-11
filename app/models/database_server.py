"""
NEXDB - Database Server model
"""

from datetime import datetime
from app import db
from cryptography.fernet import Fernet
from flask import current_app

class DatabaseServer(db.Model):
    """DatabaseServer model for MySQL and PostgreSQL servers."""
    __tablename__ = 'database_servers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    server_type = db.Column(db.String(20), nullable=False)  # mysql, postgresql
    username = db.Column(db.String(100), nullable=False)
    encrypted_password = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    
    # Relationships
    databases = db.relationship('Database', backref='server', lazy=True, 
                              cascade='all, delete-orphan')
    
    @property
    def password(self):
        """Decrypt and return the password."""
        if not self.encrypted_password:
            return None
        
        cipher_suite = Fernet(current_app.config['ENCRYPTION_KEY'].encode())
        return cipher_suite.decrypt(self.encrypted_password.encode()).decode()
    
    @password.setter
    def password(self, password):
        """Encrypt and store the password."""
        cipher_suite = Fernet(current_app.config['ENCRYPTION_KEY'].encode())
        self.encrypted_password = cipher_suite.encrypt(password.encode()).decode()
    
    def get_connection_details(self):
        """Return database connection details."""
        return {
            'host': self.host,
            'port': self.port,
            'user': self.username,
            'password': self.password,
            'type': self.server_type
        }
    
    def __repr__(self):
        return f'<DatabaseServer {self.name} ({self.server_type})>'


class Database(db.Model):
    """Database model for databases within servers."""
    __tablename__ = 'databases'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    server_id = db.Column(db.Integer, db.ForeignKey('database_servers.id'), nullable=False)
    
    # Relationships
    database_users = db.relationship('DatabaseUser', backref='database', lazy=True,
                                   cascade='all, delete-orphan')
    backups = db.relationship('Backup', backref='database', lazy=True,
                            cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Database {self.name}>'


class DatabaseUser(db.Model):
    """DatabaseUser model for users within databases."""
    __tablename__ = 'database_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    encrypted_password = db.Column(db.Text, nullable=False)
    privileges = db.Column(db.Text)  # JSON-encoded privileges
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    database_id = db.Column(db.Integer, db.ForeignKey('databases.id'), nullable=False)
    
    @property
    def password(self):
        """Decrypt and return the password."""
        if not self.encrypted_password:
            return None
        
        cipher_suite = Fernet(current_app.config['ENCRYPTION_KEY'].encode())
        return cipher_suite.decrypt(self.encrypted_password.encode()).decode()
    
    @password.setter
    def password(self, password):
        """Encrypt and store the password."""
        cipher_suite = Fernet(current_app.config['ENCRYPTION_KEY'].encode())
        self.encrypted_password = cipher_suite.encrypt(password.encode()).decode()
    
    def __repr__(self):
        return f'<DatabaseUser {self.username}>' 