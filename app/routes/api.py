from flask import jsonify, request, make_response
from app.routes import api_bp
from app.services.db_service import DBService
from app.services.backup_service import BackupService
from app.services.scheduler_service import SchedulerService
from app.services.user_service import UserService
from functools import wraps
import secrets
import os

# API authentication token (could be stored in environment variable for production)
API_TOKEN = os.environ.get('NEXDB_API_TOKEN', secrets.token_hex(16))

def require_api_token(f):
    """Decorator to require API token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('X-API-Token')
        if not token or token != API_TOKEN:
            return make_response(jsonify({'error': 'Unauthorized'}), 401)
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/token')
def get_token():
    """Get API token (for initial setup only)"""
    return jsonify({'token': API_TOKEN})

@api_bp.route('/databases', methods=['GET'])
@require_api_token
def get_databases():
    """Get all databases"""
    mysql_dbs = DBService.get_mysql_databases()
    postgres_dbs = DBService.get_postgres_databases()
    
    return jsonify({
        'mysql': mysql_dbs,
        'postgres': postgres_dbs
    })

@api_bp.route('/databases/create', methods=['POST'])
@require_api_token
def create_database():
    """Create a new database"""
    data = request.json
    if not data or 'db_type' not in data or 'db_name' not in data:
        return make_response(jsonify({'error': 'Missing required parameters'}), 400)
    
    db_type = data['db_type']
    db_name = data['db_name']
    
    result = False
    if db_type == 'mysql':
        result = DBService.create_mysql_database(db_name)
    elif db_type == 'postgres':
        result = DBService.create_postgres_database(db_name)
    else:
        return make_response(jsonify({'error': 'Invalid database type'}), 400)
    
    if result:
        return jsonify({'success': True, 'message': f'{db_type} database {db_name} created successfully'})
    else:
        return make_response(jsonify({'error': f'Failed to create {db_type} database'}), 500)

@api_bp.route('/users/create', methods=['POST'])
@require_api_token
def create_db_user():
    """Create a new database user"""
    data = request.json
    if not data or 'db_type' not in data or 'username' not in data:
        return make_response(jsonify({'error': 'Missing required parameters'}), 400)
    
    db_type = data['db_type']
    username = data['username']
    password = data.get('password', secrets.token_urlsafe(12))
    db_name = data.get('db_name')
    
    result = False
    if db_type == 'mysql':
        result = DBService.create_mysql_user(username, password, db_name)
    elif db_type == 'postgres':
        result = DBService.create_postgres_user(username, password, db_name)
    else:
        return make_response(jsonify({'error': 'Invalid database type'}), 400)
    
    if result:
        return jsonify({
            'success': True, 
            'message': f'{db_type} user {username} created successfully',
            'username': username,
            'password': password,
            'db_name': db_name
        })
    else:
        return make_response(jsonify({'error': f'Failed to create {db_type} user'}), 500)

@api_bp.route('/backups', methods=['GET'])
@require_api_token
def get_backups():
    """Get all backups"""
    backups = BackupService.get_all_backups()
    return jsonify({
        'backups': [backup.to_dict() for backup in backups]
    })

@api_bp.route('/backups/create', methods=['POST'])
@require_api_token
def create_backup():
    """Create a new backup"""
    data = request.json
    if not data or 'db_type' not in data or 'db_name' not in data:
        return make_response(jsonify({'error': 'Missing required parameters'}), 400)
    
    db_type = data['db_type']
    db_name = data['db_name']
    
    try:
        backup = BackupService.create_backup(db_type, db_name)
        if backup:
            return jsonify({
                'success': True,
                'message': f'Backup for {db_name} created successfully',
                'backup': backup.to_dict()
            })
        else:
            return make_response(jsonify({'error': 'Failed to create backup'}), 500)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)

@api_bp.route('/backups/schedule', methods=['POST'])
@require_api_token
def schedule_backup():
    """Schedule a backup"""
    data = request.json
    if not data or 'db_type' not in data or 'db_name' not in data or 'schedule' not in data:
        return make_response(jsonify({'error': 'Missing required parameters'}), 400)
    
    db_type = data['db_type']
    db_name = data['db_name']
    schedule = data['schedule']
    
    try:
        result = SchedulerService.schedule_backup(db_type, db_name, schedule)
        if result:
            return jsonify({
                'success': True,
                'message': f'Backup schedule for {db_name} created successfully',
                'schedule': result
            })
        else:
            return make_response(jsonify({'error': 'Failed to create backup schedule'}), 500)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)

@api_bp.route('/ports/open/<db_type>', methods=['POST'])
@require_api_token
def open_port(db_type):
    """Open database port"""
    if db_type not in ['mysql', 'postgres']:
        return make_response(jsonify({'error': 'Invalid database type'}), 400)
    
    result = DBService.open_port(db_type)
    
    if result:
        port = '3306' if db_type == 'mysql' else '5432'
        return jsonify({
            'success': True,
            'message': f'Port {port} opened for {db_type} successfully'
        })
    else:
        return make_response(jsonify({'error': f'Failed to open port for {db_type}'}), 500)

@api_bp.route('/status', methods=['GET'])
def status():
    """Get API status (no authentication required)"""
    return jsonify({
        'status': 'online',
        'version': os.environ.get('NEXDB_VERSION', '1.0.0')
    }) 