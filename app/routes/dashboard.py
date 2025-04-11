from flask import render_template, redirect, url_for, session, request, flash
from app.routes import dashboard_bp
from app.routes.auth import login_required

@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home page"""
    # Initialize empty collections for dashboard data
    mysql_dbs = []
    postgres_dbs = []
    recent_backups = []
    backup_schedules = []
    credentials = []
    
    # Try to load data from services if they exist
    try:
        from app.services.db_service import DBService
        mysql_dbs = DBService.get_mysql_databases()
        postgres_dbs = DBService.get_postgres_databases()
        credentials = DBService.get_all_credentials()
    except (ImportError, AttributeError):
        # Service not available or method not found
        pass
        
    try:
        from app.services.backup_service import BackupService
        recent_backups = BackupService.get_all_backups(limit=5)
    except (ImportError, AttributeError):
        # Service not available or method not found
        pass
        
    try:
        from app.services.scheduler_service import SchedulerService
        backup_schedules = SchedulerService.get_backup_schedules()
    except (ImportError, AttributeError):
        # Service not available or method not found
        pass
    
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
    mysql_dbs = []
    try:
        from app.services.db_service import DBService
        mysql_dbs = DBService.get_mysql_databases()
    except (ImportError, AttributeError):
        pass
        
    return render_template('dashboard/mysql.html', 
                          databases=mysql_dbs,
                          theme=session.get('theme', 'light'))

@dashboard_bp.route('/postgres')
@login_required
def postgres_overview():
    """PostgreSQL dashboard page"""
    postgres_dbs = []
    try:
        from app.services.db_service import DBService
        postgres_dbs = DBService.get_postgres_databases()
    except (ImportError, AttributeError):
        pass
        
    return render_template('dashboard/postgres.html', 
                          databases=postgres_dbs,
                          theme=session.get('theme', 'light'))

@dashboard_bp.route('/stats')
@login_required
def stats():
    """System statistics dashboard"""
    # Default values
    mysql_count = 0
    postgres_count = 0
    backup_count = 0
    total_backup_size = 0
    scheduled_count = 0
    credential_count = 0
    
    # Try to load real data if services exist
    try:
        from app.services.db_service import DBService
        mysql_dbs = DBService.get_mysql_databases()
        postgres_dbs = DBService.get_postgres_databases()
        mysql_count = len(mysql_dbs) if mysql_dbs else 0
        postgres_count = len(postgres_dbs) if postgres_dbs else 0
        credentials = DBService.get_all_credentials()
        credential_count = len(credentials) if credentials else 0
    except (ImportError, AttributeError):
        pass
        
    try:
        from app.services.backup_service import BackupService
        backups = BackupService.get_all_backups()
        backup_count = len(backups) if backups else 0
        total_backup_size = sum(b.file_size for b in backups if hasattr(b, 'file_size') and b.file_size) if backups else 0
    except (ImportError, AttributeError):
        pass
        
    try:
        from app.services.scheduler_service import SchedulerService
        schedules = SchedulerService.get_backup_schedules()
        scheduled_count = len(schedules) if schedules else 0
    except (ImportError, AttributeError):
        pass
    
    return render_template('dashboard/stats.html',
                          mysql_count=mysql_count,
                          postgres_count=postgres_count,
                          backup_count=backup_count,
                          total_backup_size=total_backup_size,
                          scheduled_count=scheduled_count,
                          credential_count=credential_count,
                          theme=session.get('theme', 'light')) 