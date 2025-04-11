"""
NEXDB - CLI commands
"""

import click
import os
from flask.cli import with_appcontext
from datetime import datetime
from app import db

def register_cli_commands(app):
    """Register custom CLI commands with the Flask application."""
    
    @app.cli.command('init-db')
    @with_appcontext
    def init_db():
        """Initialize the application database."""
        db.create_all()
        click.echo('Database initialized.')
    
    @app.cli.command('create-admin')
    @click.argument('username')
    @click.argument('email')
    @click.argument('password')
    @with_appcontext
    def create_admin(username, email, password):
        """Create an admin user."""
        from app.models.user import User, Role
        
        # Check if admin role exists
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin', description='Administrator')
            db.session.add(admin_role)
        
        # Create user if doesn't exist
        user = User.query.filter_by(email=email).first()
        if user:
            click.echo(f'User with email {email} already exists.')
            return
        
        user = User(
            username=username,
            email=email,
            password=password,
            active=True,
            roles=[admin_role]
        )
        db.session.add(user)
        db.session.commit()
        click.echo(f'Admin user {username} created successfully.')
    
    @app.cli.command('backup-all')
    @with_appcontext
    def backup_all():
        """Backup all databases."""
        from app.backup.utils import backup_all_databases
        backup_all_databases()
        click.echo('Backup completed.')
    
    @app.cli.command('test-s3')
    @with_appcontext
    def test_s3():
        """Test S3 connection."""
        from app.backup.utils import test_s3_connection
        result = test_s3_connection()
        if result:
            click.echo('S3 connection successful.')
        else:
            click.echo('S3 connection failed. Please check your credentials.')
    
    @app.cli.command('create-sample-data')
    @with_appcontext
    def create_sample_data():
        """Create sample data for development."""
        from app.models.user import User, Role
        from app.models.project import Project
        from app.models.database_server import DatabaseServer
        
        # Create roles
        admin_role = Role.query.filter_by(name='admin').first() or Role(name='admin', description='Administrator')
        user_role = Role.query.filter_by(name='user').first() or Role(name='user', description='Regular user')
        
        if not Role.query.filter_by(name='admin').first():
            db.session.add(admin_role)
        
        if not Role.query.filter_by(name='user').first():
            db.session.add(user_role)
        
        # Create admin user
        admin_user = User.query.filter_by(email='admin@example.com').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password='adminpassword',
                active=True,
                roles=[admin_role]
            )
            db.session.add(admin_user)
        
        # Create regular user
        regular_user = User.query.filter_by(email='user@example.com').first()
        if not regular_user:
            regular_user = User(
                username='user',
                email='user@example.com',
                password='userpassword',
                active=True,
                roles=[user_role]
            )
            db.session.add(regular_user)
        
        # Create projects
        project1 = Project.query.filter_by(name='Sample Project 1').first()
        if not project1:
            project1 = Project(
                name='Sample Project 1',
                description='A sample project for development',
                created_by=admin_user.id
            )
            db.session.add(project1)
        
        project2 = Project.query.filter_by(name='Sample Project 2').first()
        if not project2:
            project2 = Project(
                name='Sample Project 2',
                description='Another sample project',
                created_by=regular_user.id
            )
            db.session.add(project2)
        
        # Create database servers
        mysql_server = DatabaseServer.query.filter_by(name='Local MySQL').first()
        if not mysql_server:
            mysql_server = DatabaseServer(
                name='Local MySQL',
                host='localhost',
                port=3306,
                server_type='mysql',
                username='root',
                password='example',  # Not secure, for development only
                project_id=project1.id if Project.query.filter_by(name='Sample Project 1').first() else None
            )
            db.session.add(mysql_server)
        
        postgres_server = DatabaseServer.query.filter_by(name='Local PostgreSQL').first()
        if not postgres_server:
            postgres_server = DatabaseServer(
                name='Local PostgreSQL',
                host='localhost',
                port=5432,
                server_type='postgresql',
                username='postgres',
                password='example',  # Not secure, for development only
                project_id=project2.id if Project.query.filter_by(name='Sample Project 2').first() else None
            )
            db.session.add(postgres_server)
        
        db.session.commit()
        click.echo('Sample data created successfully.') 