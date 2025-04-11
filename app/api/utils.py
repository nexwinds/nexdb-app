"""
NEXDB - API utilities
"""

from functools import wraps
from flask import jsonify, request, g
from flask_jwt_extended import get_jwt_identity
import pymysql
import psycopg2
import re
import json
import logging
from app.models import User, Project

def admin_required(fn):
    """Decorator for API routes that require admin privileges."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.has_role('admin'):
            return jsonify(error="Admin privileges required"), 403
        
        return fn(*args, **kwargs)
    return wrapper


def validate_input(required_fields=None, string_fields=None, numeric_fields=None, boolean_fields=None):
    """Validate request JSON data."""
    data = request.json
    
    if data is None:
        return {'valid': False, 'error': 'No JSON data provided'}
    
    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                return {'valid': False, 'error': f"Field '{field}' is required"}
    
    # Validate string fields
    if string_fields:
        for field in string_fields:
            if field in data and data[field] is not None:
                if not isinstance(data[field], str):
                    return {'valid': False, 'error': f"Field '{field}' must be a string"}
    
    # Validate numeric fields
    if numeric_fields:
        for field in numeric_fields:
            if field in data and data[field] is not None:
                if not isinstance(data[field], (int, float)):
                    return {'valid': False, 'error': f"Field '{field}' must be a number"}
    
    # Validate boolean fields
    if boolean_fields:
        for field in boolean_fields:
            if field in data and data[field] is not None:
                if not isinstance(data[field], bool):
                    return {'valid': False, 'error': f"Field '{field}' must be a boolean"}
    
    return {'valid': True}


def sanitize_sql_identifier(identifier):
    """Sanitize SQL identifiers (table names, column names, etc.)."""
    # Only allow alphanumeric characters and underscores
    if not re.match(r'^[a-zA-Z0-9_]+$', identifier):
        raise ValueError(f"Invalid SQL identifier: {identifier}")
    
    return identifier


def handle_database_connection(server):
    """Test connection to a database server."""
    try:
        if server.server_type == 'mysql':
            conn = pymysql.connect(
                host=server.host,
                port=server.port,
                user=server.username,
                password=server.password,
                connect_timeout=5
            )
            conn.close()
            return {'success': True}
        
        elif server.server_type == 'postgresql':
            conn = psycopg2.connect(
                host=server.host,
                port=server.port,
                user=server.username,
                password=server.password,
                connect_timeout=5
            )
            conn.close()
            return {'success': True}
        
        else:
            return {'success': False, 'message': f"Unsupported database type: {server.server_type}"}
    
    except (pymysql.Error, psycopg2.Error) as e:
        return {'success': False, 'message': str(e)}
    except Exception as e:
        logging.error(f"Database connection error: {str(e)}")
        return {'success': False, 'message': 'Failed to connect to database server'}


def execute_query(server, query, params=None):
    """Execute a query on a database server."""
    try:
        if server.server_type == 'mysql':
            conn = pymysql.connect(
                host=server.host,
                port=server.port,
                user=server.username,
                password=server.password
            )
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith(('SELECT', 'SHOW')):
                columns = [col[0] for col in cursor.description]
                result = [dict(zip(columns, row)) for row in cursor.fetchall()]
                cursor.close()
                conn.close()
                return {'success': True, 'result': result}
            else:
                conn.commit()
                affected_rows = cursor.rowcount
                cursor.close()
                conn.close()
                return {'success': True, 'affected_rows': affected_rows}
        
        elif server.server_type == 'postgresql':
            conn = psycopg2.connect(
                host=server.host,
                port=server.port,
                user=server.username,
                password=server.password
            )
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith(('SELECT', 'SHOW')):
                columns = [col.name for col in cursor.description]
                result = [dict(zip(columns, row)) for row in cursor.fetchall()]
                cursor.close()
                conn.close()
                return {'success': True, 'result': result}
            else:
                conn.commit()
                affected_rows = cursor.rowcount
                cursor.close()
                conn.close()
                return {'success': True, 'affected_rows': affected_rows}
        
        else:
            return {'success': False, 'message': f"Unsupported database type: {server.server_type}"}
    
    except (pymysql.Error, psycopg2.Error) as e:
        return {'success': False, 'message': str(e)}
    except Exception as e:
        logging.error(f"Query execution error: {str(e)}")
        return {'success': False, 'message': 'Failed to execute query'} 