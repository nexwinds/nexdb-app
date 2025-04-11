"""
NEXDB - Backup utilities
"""

import os
import subprocess
import tempfile
import boto3
import json
import logging
from datetime import datetime
from flask import current_app
from app import db, scheduler
from app.models import Database, Backup, DatabaseServer

def create_backup(database_id):
    """Create a backup of a database."""
    try:
        # Get database
        database = Database.query.get(database_id)
        if not database:
            return {'success': False, 'message': 'Database not found'}
        
        server = database.server
        
        # Create temporary directory for backup
        backup_dir = tempfile.mkdtemp()
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{database.name}_{timestamp}.sql"
        backup_path = os.path.join(backup_dir, filename)
        
        # Create backup record
        backup = Backup(
            filename=filename,
            database_id=database.id,
            status='pending'
        )
        db.session.add(backup)
        db.session.commit()
        
        # Perform backup based on database type
        if server.server_type == 'mysql':
            result = backup_mysql(server, database.name, backup_path)
        elif server.server_type == 'postgresql':
            result = backup_postgresql(server, database.name, backup_path)
        else:
            return {
                'success': False, 
                'message': f"Unsupported database type: {server.server_type}"
            }
        
        if not result['success']:
            # Update backup status to failed
            backup.status = 'failed'
            backup.metadata_dict = {'error': result['message']}
            db.session.commit()
            return result
        
        # Update backup record with file size
        backup.size_bytes = os.path.getsize(backup_path)
        backup.status = 'completed'
        backup.metadata_dict = {
            'backup_time': datetime.utcnow().isoformat(),
            'server_type': server.server_type,
            'server_host': server.host,
            'database_name': database.name
        }
        db.session.commit()
        
        return {
            'success': True,
            'backup_id': backup.id,
            'path': backup_path
        }
    
    except Exception as e:
        logging.error(f"Backup error: {str(e)}")
        return {'success': False, 'message': f"Backup failed: {str(e)}"}


def backup_mysql(server, database_name, backup_path):
    """Create MySQL database backup."""
    try:
        cmd = [
            'mysqldump',
            f'--host={server.host}',
            f'--port={server.port}',
            f'--user={server.username}',
            f'--password={server.password}',
            '--single-transaction',
            '--routines',
            '--triggers',
            '--events',
            database_name
        ]
        
        with open(backup_path, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True, text=True)
        
        if result.returncode != 0:
            return {'success': False, 'message': result.stderr}
        
        return {'success': True}
    
    except subprocess.CalledProcessError as e:
        return {'success': False, 'message': e.stderr}
    except Exception as e:
        return {'success': False, 'message': str(e)}


def backup_postgresql(server, database_name, backup_path):
    """Create PostgreSQL database backup."""
    try:
        # Set environment variables for pg_dump
        env = os.environ.copy()
        env['PGPASSWORD'] = server.password
        
        cmd = [
            'pg_dump',
            f'--host={server.host}',
            f'--port={server.port}',
            f'--username={server.username}',
            '--format=plain',
            '--clean',
            '--create',
            '--if-exists',
            database_name
        ]
        
        with open(backup_path, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True, text=True, env=env)
        
        if result.returncode != 0:
            return {'success': False, 'message': result.stderr}
        
        return {'success': True}
    
    except subprocess.CalledProcessError as e:
        return {'success': False, 'message': e.stderr}
    except Exception as e:
        return {'success': False, 'message': str(e)}


def upload_to_s3(backup_id):
    """Upload a backup to S3."""
    try:
        # Get backup
        backup = Backup.query.get(backup_id)
        if not backup:
            return {'success': False, 'message': 'Backup not found'}
        
        # Check if already uploaded
        if backup.location == 's3':
            return {'success': True, 'message': 'Backup already on S3'}
        
        # Get backup file path
        backup_dir = current_app.config.get('BACKUP_DIR', '/tmp')
        backup_path = os.path.join(backup_dir, backup.filename)
        
        # Check if file exists
        if not os.path.exists(backup_path):
            return {'success': False, 'message': 'Backup file not found'}
        
        # Get S3 configuration
        bucket_name = current_app.config.get('S3_BUCKET')
        if not bucket_name:
            return {'success': False, 'message': 'S3 bucket not configured'}
        
        # Upload to S3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=current_app.config.get('S3_ACCESS_KEY'),
            aws_secret_access_key=current_app.config.get('S3_SECRET_KEY'),
            region_name=current_app.config.get('S3_REGION')
        )
        
        # Create S3 object key
        database = Database.query.get(backup.database_id)
        server = database.server if database else None
        project_id = server.project_id if server else 'unknown'
        s3_key = f"backups/project_{project_id}/database_{backup.database_id}/{backup.filename}"
        
        # Upload file
        s3_client.upload_file(backup_path, bucket_name, s3_key)
        
        # Update backup record
        backup.location = 's3'
        backup.s3_path = s3_key
        db.session.commit()
        
        return {'success': True, 's3_path': s3_key}
    
    except Exception as e:
        logging.error(f"S3 upload error: {str(e)}")
        return {'success': False, 'message': f"S3 upload failed: {str(e)}"}


def backup_all_databases():
    """Backup all databases (for scheduled backups)."""
    try:
        databases = Database.query.all()
        results = []
        
        for database in databases:
            # Check if there's a backup schedule enabled
            if not any(schedule.enabled for schedule in database.backup_schedules):
                continue
            
            # Perform backup
            result = create_backup(database.id)
            
            # Upload to S3 if configured
            if result.get('success') and any(schedule.upload_to_s3 for schedule in database.backup_schedules):
                upload_result = upload_to_s3(result.get('backup_id'))
                result['s3_upload'] = upload_result
            
            results.append({
                'database_id': database.id,
                'database_name': database.name,
                'result': result
            })
        
        return {'success': True, 'results': results}
    
    except Exception as e:
        logging.error(f"Backup all databases error: {str(e)}")
        return {'success': False, 'message': f"Backup failed: {str(e)}"}


def test_s3_connection():
    """Test S3 connection."""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=current_app.config.get('S3_ACCESS_KEY'),
            aws_secret_access_key=current_app.config.get('S3_SECRET_KEY'),
            region_name=current_app.config.get('S3_REGION')
        )
        
        # List buckets to test connection
        s3_client.list_buckets()
        return True
    except Exception as e:
        logging.error(f"S3 connection test error: {str(e)}")
        return False


def setup_backup_scheduler(app):
    """Set up backup scheduler jobs."""
    with app.app_context():
        from app.models import BackupSchedule
        
        # Remove all existing jobs
        scheduler.remove_all_jobs()
        
        # Get all backup schedules
        schedules = BackupSchedule.query.filter_by(enabled=True).all()
        
        for schedule in schedules:
            if schedule.frequency == 'daily':
                scheduler.add_job(
                    id=f"backup_{schedule.id}",
                    func=create_backup,
                    args=[schedule.database_id],
                    trigger='cron',
                    hour=schedule.time.hour,
                    minute=schedule.time.minute
                )
            elif schedule.frequency == 'weekly':
                scheduler.add_job(
                    id=f"backup_{schedule.id}",
                    func=create_backup,
                    args=[schedule.database_id],
                    trigger='cron',
                    day_of_week=schedule.day_of_week,
                    hour=schedule.time.hour,
                    minute=schedule.time.minute
                )
            elif schedule.frequency == 'monthly':
                scheduler.add_job(
                    id=f"backup_{schedule.id}",
                    func=create_backup,
                    args=[schedule.database_id],
                    trigger='cron',
                    day=schedule.day_of_month,
                    hour=schedule.time.hour,
                    minute=schedule.time.minute
                ) 