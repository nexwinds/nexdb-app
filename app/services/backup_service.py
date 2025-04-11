import os
import subprocess
import datetime
import boto3
from app.models import db
from app.models.backup import Backup
from config import BACKUP_DIR, S3_ENABLED, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY, S3_REGION

class BackupService:
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
    def get_all_backups(limit=None):
        """Get all backups with optional limit"""
        query = Backup.query.order_by(Backup.created_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def get_backup_by_id(backup_id):
        """Get a backup by ID"""
        return Backup.query.get(backup_id)
    
    @staticmethod
    def delete_backup(backup_id):
        """Delete a backup by ID"""
        backup = Backup.query.get(backup_id)
        if backup:
            # Delete the file if it exists
            if os.path.exists(backup.file_path):
                os.remove(backup.file_path)
            
            # Delete the record
            db.session.delete(backup)
            db.session.commit()
            return True
        return False 