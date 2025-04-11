import os
import subprocess
import datetime
import boto3
from app.models import db
from app.models.backup import Backup
from config import BACKUP_DIR, S3_ENABLED, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY, S3_REGION
import shutil

class Backup:
    """Simple backup model"""
    def __init__(self, id, db_name, db_type, file_path, created_at, file_size=0):
        self.id = id
        self.db_name = db_name
        self.db_type = db_type  # 'mysql' or 'postgres'
        self.file_path = file_path
        self.created_at = created_at
        self.file_size = file_size

class BackupService:
    """Service for database backups"""
    # In-memory backup storage (for development/fallback)
    _backups = []
    _backup_dir = os.environ.get('NEXDB_BACKUP_DIR', '/opt/nexdb/backups')
    
    @classmethod
    def get_all_backups(cls, limit=None):
        """Get all backups, optionally limited"""
        # Sort by creation date, newest first
        sorted_backups = sorted(
            cls._backups, 
            key=lambda b: b.created_at if hasattr(b, 'created_at') else datetime.datetime.now(),
            reverse=True
        )
        
        if limit:
            return sorted_backups[:limit]
        return sorted_backups
    
    @classmethod
    def create_mysql_backup(cls, db_name):
        """Create a MySQL database backup"""
        # Ensure backup directory exists
        os.makedirs(cls._backup_dir, exist_ok=True)
        
        # Generate backup file path
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = os.path.join(cls._backup_dir, f"{db_name}_mysql_{timestamp}.sql")
        
        try:
            # Execute mysqldump command
            result = subprocess.run(
                ['mysqldump', db_name, '-r', file_path],
                capture_output=True, check=False
            )
            
            if result.returncode == 0 and os.path.exists(file_path):
                # Get file size
                file_size = os.path.getsize(file_path)
                
                # Create backup record
                next_id = max([b.id for b in cls._backups], default=0) + 1
                backup = Backup(
                    id=next_id,
                    db_name=db_name,
                    db_type='mysql',
                    file_path=file_path,
                    created_at=datetime.datetime.now(),
                    file_size=file_size
                )
                
                # Add to in-memory storage
                cls._backups.append(backup)
                
                return backup
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        return None
    
    @classmethod
    def create_postgres_backup(cls, db_name):
        """Create a PostgreSQL database backup"""
        # Ensure backup directory exists
        os.makedirs(cls._backup_dir, exist_ok=True)
        
        # Generate backup file path
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = os.path.join(cls._backup_dir, f"{db_name}_postgres_{timestamp}.sql")
        
        try:
            # Execute pg_dump command
            result = subprocess.run(
                ['pg_dump', '-f', file_path, db_name],
                capture_output=True, check=False
            )
            
            if result.returncode == 0 and os.path.exists(file_path):
                # Get file size
                file_size = os.path.getsize(file_path)
                
                # Create backup record
                next_id = max([b.id for b in cls._backups], default=0) + 1
                backup = Backup(
                    id=next_id,
                    db_name=db_name,
                    db_type='postgres',
                    file_path=file_path,
                    created_at=datetime.datetime.now(),
                    file_size=file_size
                )
                
                # Add to in-memory storage
                cls._backups.append(backup)
                
                return backup
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        return None
    
    @classmethod
    def delete_backup(cls, backup_id):
        """Delete a backup by ID"""
        backup = None
        for b in cls._backups:
            if b.id == backup_id:
                backup = b
                break
                
        if backup and os.path.exists(backup.file_path):
            try:
                # Remove the file
                os.remove(backup.file_path)
                
                # Remove from in-memory storage
                cls._backups.remove(backup)
                
                return True
            except (OSError, ValueError):
                pass
                
        return False

    @staticmethod
    def create_backup(db_type, db_name, user_id=None):
        """Create a database backup"""
        # Create backup filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{db_name}_{db_type}_{timestamp}.sql"
        filepath = os.path.join(BACKUP_DIR, filename)
        
        # Ensure backup directory exists
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Create new backup record
        backup = Backup(
            db_type=db_type,
            db_name=db_name,
            file_path=filepath,
            created_by=user_id,
            status='in_progress'
        )
        db.session.add(backup)
        db.session.commit()
        
        try:
            # Perform the actual backup
            if db_type == 'mysql':
                cmd = f"mysqldump -u root {db_name} > {filepath}"
            elif db_type == 'postgres':
                cmd = f"pg_dump -U postgres {db_name} > {filepath}"
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            result = subprocess.run(cmd, shell=True, check=True)
            
            # Update backup record
            file_size = os.path.getsize(filepath)
            backup.file_size = file_size
            backup.status = 'completed'
            
            # Upload to S3 if enabled
            if S3_ENABLED:
                s3_path = BackupService.upload_to_s3(filepath, filename)
                if s3_path:
                    backup.s3_uploaded = True
                    backup.s3_path = s3_path
            
            db.session.commit()
            return backup
            
        except Exception as e:
            backup.status = 'failed'
            db.session.commit()
            raise e
    
    @staticmethod
    def upload_to_s3(file_path, file_name):
        """Upload a file to S3"""
        if not S3_ENABLED or not S3_BUCKET:
            return None
        
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=S3_ACCESS_KEY,
                aws_secret_access_key=S3_SECRET_KEY,
                region_name=S3_REGION
            )
            
            # Upload file
            s3_path = f"backups/{file_name}"
            s3_client.upload_file(file_path, S3_BUCKET, s3_path)
            return s3_path
        except Exception as e:
            print(f"S3 upload failed: {str(e)}")
            return None
    
    @staticmethod
    def get_backup_by_id(backup_id):
        """Get a backup by ID"""
        return Backup.query.get(backup_id) 