"""
NEXDB - API routes
"""

from flask import Blueprint, jsonify, request, current_app, url_for
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from app import db, limiter
from app.models import User, Project, DatabaseServer, Database, DatabaseUser, Backup, BackupSchedule
from app.api.utils import admin_required, validate_input, handle_database_connection
from app.backup.utils import create_backup, upload_to_s3
import json
from datetime import datetime, timedelta

# Create Blueprint
api_bp = Blueprint('api', __name__)

# Global API rate limiting
@api_bp.before_request
def check_basic_auth():
    """Check if API access is enabled."""
    if not current_app.config.get('API_ENABLED', True):
        return jsonify(error="API access is disabled"), 503


# Authentication endpoints
@api_bp.route('/auth/token', methods=['POST'])
@limiter.limit("10 per minute")
def get_token():
    """Get JWT token for API authentication."""
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    if not username or not password:
        return jsonify(error="Missing username or password"), 400
    
    user = User.query.filter_by(username=username).first()
    if not user or not user.verify_password(password):
        return jsonify(error="Invalid credentials"), 401
    
    if not user.active:
        return jsonify(error="Account is deactivated"), 403
    
    # Generate access token
    access_token = create_access_token(identity=user.id)
    
    return jsonify(access_token=access_token, user_id=user.id, username=user.username)


# Project endpoints
@api_bp.route('/projects', methods=['GET'])
@jwt_required()
def get_projects():
    """Get all projects for the current user."""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    # Get user's projects (either created by or member of)
    created_projects = Project.query.filter_by(created_by=user.id).all()
    member_projects = user.member_projects
    
    # Combine and deduplicate projects
    all_projects = set(created_projects) | set(member_projects)
    
    projects = []
    for project in all_projects:
        projects.append({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'created_at': project.created_at.isoformat(),
            'access_level': project.get_member_access_level(user.id) or 'owner' 
                           if project.created_by == user.id else 'read'
        })
    
    return jsonify(projects=projects)


@api_bp.route('/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """Get a specific project."""
    user_id = get_jwt_identity()
    project = Project.query.get_or_404(project_id)
    
    # Check if user has access to this project
    user = User.query.get_or_404(user_id)
    if project.created_by != user.id and user not in project.members:
        return jsonify(error="Access denied"), 403
    
    # Get project details
    project_data = {
        'id': project.id,
        'name': project.name,
        'description': project.description,
        'created_at': project.created_at.isoformat(),
        'created_by': project.created_by,
        'database_servers': [],
        'members': []
    }
    
    # Get server details
    for server in project.database_servers:
        project_data['database_servers'].append({
            'id': server.id,
            'name': server.name,
            'host': server.host,
            'port': server.port,
            'server_type': server.server_type
        })
    
    # Get member details
    for member in project.members:
        project_data['members'].append({
            'id': member.id,
            'username': member.username,
            'email': member.email,
            'access_level': project.get_member_access_level(member.id)
        })
    
    return jsonify(project=project_data)


@api_bp.route('/projects', methods=['POST'])
@jwt_required()
def create_project():
    """Create a new project."""
    user_id = get_jwt_identity()
    
    # Validate input
    data = request.json
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return jsonify(error="Project name is required"), 400
    
    # Create project
    project = Project(
        name=name,
        description=description,
        created_by=user_id
    )
    
    db.session.add(project)
    db.session.commit()
    
    return jsonify(
        message="Project created successfully",
        project_id=project.id
    ), 201


@api_bp.route('/projects/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """Update a project."""
    user_id = get_jwt_identity()
    project = Project.query.get_or_404(project_id)
    
    # Check if user has permission to edit
    if project.created_by != user_id and \
       project.get_member_access_level(user_id) not in ['admin', 'write']:
        return jsonify(error="Permission denied"), 403
    
    # Update project details
    data = request.json
    if 'name' in data:
        project.name = data['name']
    if 'description' in data:
        project.description = data['description']
    
    db.session.commit()
    
    return jsonify(message="Project updated successfully")


@api_bp.route('/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """Delete a project."""
    user_id = get_jwt_identity()
    project = Project.query.get_or_404(project_id)
    
    # Check if user has permission to delete (only creator or admin)
    if project.created_by != user_id and \
       project.get_member_access_level(user_id) != 'admin':
        return jsonify(error="Permission denied"), 403
    
    db.session.delete(project)
    db.session.commit()
    
    return jsonify(message="Project deleted successfully")


# Database server endpoints
@api_bp.route('/projects/<int:project_id>/servers', methods=['POST'])
@jwt_required()
def create_server(project_id):
    """Create a new database server in a project."""
    user_id = get_jwt_identity()
    project = Project.query.get_or_404(project_id)
    
    # Check if user has permission to add server
    if project.created_by != user_id and \
       project.get_member_access_level(user_id) not in ['admin', 'write']:
        return jsonify(error="Permission denied"), 403
    
    # Validate input
    data = request.json
    required_fields = ['name', 'host', 'port', 'server_type', 'username', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"{field} is required"), 400
    
    # Validate server_type
    if data['server_type'] not in ['mysql', 'postgresql']:
        return jsonify(error="Server type must be 'mysql' or 'postgresql'"), 400
    
    # Create server
    server = DatabaseServer(
        name=data['name'],
        host=data['host'],
        port=data['port'],
        server_type=data['server_type'],
        username=data['username'],
        password=data['password'],
        description=data.get('description', ''),
        project_id=project.id
    )
    
    # Test connection
    try:
        connection_result = handle_database_connection(server)
        if not connection_result['success']:
            return jsonify(error=f"Could not connect to database server: {connection_result['message']}"), 400
    except Exception as e:
        return jsonify(error=f"Connection test failed: {str(e)}"), 400
    
    db.session.add(server)
    db.session.commit()
    
    return jsonify(
        message="Database server created successfully",
        server_id=server.id
    ), 201


@api_bp.route('/servers/<int:server_id>', methods=['GET'])
@jwt_required()
def get_server(server_id):
    """Get database server details."""
    user_id = get_jwt_identity()
    server = DatabaseServer.query.get_or_404(server_id)
    project = server.project
    
    # Check if user has access to the server's project
    if project.created_by != user_id and user_id not in [m.id for m in project.members]:
        return jsonify(error="Access denied"), 403
    
    # Get server details
    server_data = {
        'id': server.id,
        'name': server.name,
        'description': server.description,
        'host': server.host,
        'port': server.port,
        'server_type': server.server_type,
        'username': server.username,
        'project_id': server.project_id,
        'databases': []
    }
    
    # Get databases
    for db_obj in server.databases:
        server_data['databases'].append({
            'id': db_obj.id,
            'name': db_obj.name,
            'description': db_obj.description
        })
    
    return jsonify(server=server_data)


# Additional endpoints would be added for:
# - Database management
# - Database user management
# - Backup operations
# - Backup scheduling
# - UFW configuration
# Etc. 