"""
NEXDB - Project model
"""

from datetime import datetime
from app import db
from sqlalchemy.ext.associationproxy import association_proxy

# Association table for project users (many-to-many)
project_users = db.Table('project_users',
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('access_level', db.String(20), default='read')  # read, write, admin
)

class Project(db.Model):
    """Project model for organizing database servers and databases."""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    database_servers = db.relationship('DatabaseServer', backref='project', lazy=True)
    members = db.relationship(
        'User',
        secondary=project_users,
        lazy='subquery',
        backref=db.backref('member_projects', lazy=True)
    )
    
    def add_member(self, user, access_level='read'):
        """Add a user to the project with specified access level."""
        if not any(member.id == user.id for member in self.members):
            self.members.append(user)
            db.session.execute(
                project_users.update().
                where(project_users.c.project_id == self.id).
                where(project_users.c.user_id == user.id).
                values(access_level=access_level)
            )
    
    def remove_member(self, user):
        """Remove a user from the project."""
        if any(member.id == user.id for member in self.members):
            self.members.remove(user)
    
    def get_member_access_level(self, user_id):
        """Get the access level of a project member."""
        result = db.session.execute(
            db.select([project_users.c.access_level]).
            where(project_users.c.project_id == self.id).
            where(project_users.c.user_id == user_id)
        ).fetchone()
        return result[0] if result else None
    
    def __repr__(self):
        return f'<Project {self.name}>' 