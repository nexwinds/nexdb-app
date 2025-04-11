from flask import render_template, redirect, url_for, session
from app.routes import dashboard_bp
from app.routes.auth import login_required
from app.services.db_service import DBService
from app.services.backup_service import BackupService
from app.services.scheduler_service import SchedulerService

@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home page"""
    # Get MySQL and PostgreSQL databases
    mysql_dbs = DBService.get_mysql_databases()
    postgres_dbs = DBService.get_postgres_databases()
    
    # Get recent backups
    recent_backups = BackupService.get_all_backups(limit=5)
    
    # Get backup schedules
    backup_schedules = SchedulerService.get_backup_schedules()
    
    # Get credentials
    credentials = DBService.get_all_credentials()
    
    return render_template('dashboard/index.html',
                          mysql_dbs=mysql_dbs,
                          postgres_dbs=postgres_dbs,
                          recent_backups=recent_backups,
                          backup_schedules=backup_schedules,
                          credentials=credentials,
                          theme=session.get('theme', 'light'))

@dashboard_bp.route('/mysql')
@login_required
def mysql_overview():
    """MySQL dashboard page"""
    mysql_dbs = DBService.get_mysql_databases()
    return render_template('dashboard/mysql.html', 
                          databases=mysql_dbs,
                          theme=session.get('theme', 'light'))

@dashboard_bp.route('/postgres')
@login_required
def postgres_overview():
    """PostgreSQL dashboard page"""
    postgres_dbs = DBService.get_postgres_databases()
    return render_template('dashboard/postgres.html', 
                          databases=postgres_dbs,
                          theme=session.get('theme', 'light'))

@dashboard_bp.route('/stats')
@login_required
def stats():
    """System statistics dashboard"""
    # Get count of databases
    mysql_count = len(DBService.get_mysql_databases())
    postgres_count = len(DBService.get_postgres_databases())
    
    # Get count of backups
    backups = BackupService.get_all_backups()
    backup_count = len(backups)
    
    # Calculate total backup size
    total_backup_size = sum(b.file_size for b in backups if b.file_size)
    
    # Get count of scheduled backups
    scheduled_count = len(SchedulerService.get_backup_schedules())
    
    # Get count of credentials
    credential_count = len(DBService.get_all_credentials())
    
    return render_template('dashboard/stats.html',
                          mysql_count=mysql_count,
                          postgres_count=postgres_count,
                          backup_count=backup_count,
                          total_backup_size=total_backup_size,
                          scheduled_count=scheduled_count,
                          credential_count=credential_count,
                          theme=session.get('theme', 'light')) 