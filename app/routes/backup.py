from flask import render_template, request, redirect, url_for, flash, session, send_file
from app.routes import backup_bp
from app.routes.auth import login_required, admin_required
from app.services.backup_service import BackupService
from app.services.scheduler_service import SchedulerService
import os

@backup_bp.route('/')
@login_required
def index():
    """Backup management page"""
    backups = BackupService.get_all_backups()
    backup_schedules = SchedulerService.get_backup_schedules()
    
    return render_template('backup/index.html', 
                          backups=backups,
                          backup_schedules=backup_schedules,
                          theme=session.get('theme', 'light'))

@backup_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_backup():
    """Create a new backup"""
    if request.method == 'POST':
        db_type = request.form.get('db_type')
        db_name = request.form.get('db_name')
        
        if not db_type or not db_name:
            flash('Database type and name are required', 'danger')
            return redirect(url_for('backup.create_backup'))
        
        try:
            backup = BackupService.create_backup(
                db_type=db_type,
                db_name=db_name,
                user_id=session.get('user_id')
            )
            
            if backup:
                flash(f'Backup for {db_name} created successfully', 'success')
                return redirect(url_for('backup.index'))
            else:
                flash('Failed to create backup', 'danger')
        except Exception as e:
            flash(f'Error creating backup: {str(e)}', 'danger')
    
    return render_template('backup/create.html', theme=session.get('theme', 'light'))

@backup_bp.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule_backup():
    """Schedule a new backup"""
    if request.method == 'POST':
        db_type = request.form.get('db_type')
        db_name = request.form.get('db_name')
        schedule = request.form.get('schedule')
        
        if not db_type or not db_name or not schedule:
            flash('All fields are required', 'danger')
            return redirect(url_for('backup.schedule_backup'))
        
        try:
            result = SchedulerService.schedule_backup(
                db_type=db_type,
                db_name=db_name,
                schedule=schedule,
                user_id=session.get('user_id')
            )
            
            if result:
                flash(f'Backup schedule for {db_name} created successfully', 'success')
                return redirect(url_for('backup.index'))
            else:
                flash('Failed to create backup schedule', 'danger')
        except Exception as e:
            flash(f'Error creating backup schedule: {str(e)}', 'danger')
    
    return render_template('backup/schedule.html', theme=session.get('theme', 'light'))

@backup_bp.route('/download/<int:backup_id>')
@login_required
def download_backup(backup_id):
    """Download a backup file"""
    backup = BackupService.get_backup_by_id(backup_id)
    
    if not backup:
        flash('Backup not found', 'danger')
        return redirect(url_for('backup.index'))
    
    if not os.path.exists(backup.file_path):
        flash('Backup file not found', 'danger')
        return redirect(url_for('backup.index'))
    
    return send_file(
        backup.file_path,
        as_attachment=True,
        download_name=os.path.basename(backup.file_path)
    )

@backup_bp.route('/delete/<int:backup_id>')
@login_required
def delete_backup(backup_id):
    """Delete a backup"""
    result = BackupService.delete_backup(backup_id)
    
    if result:
        flash('Backup deleted successfully', 'success')
    else:
        flash('Failed to delete backup', 'danger')
    
    return redirect(url_for('backup.index'))

@backup_bp.route('/delete-schedule/<db_type>/<db_name>')
@login_required
def delete_schedule(db_type, db_name):
    """Delete a backup schedule"""
    result = SchedulerService.delete_backup_schedule(db_type, db_name)
    
    if result:
        flash('Backup schedule deleted successfully', 'success')
    else:
        flash('Failed to delete backup schedule', 'danger')
    
    return redirect(url_for('backup.index'))

@backup_bp.route('/s3-settings', methods=['GET', 'POST'])
@admin_required
def s3_settings():
    """Configure S3 backup settings"""
    # This would be implemented to update the S3 settings in the config
    flash('S3 settings functionality is not yet implemented', 'warning')
    return redirect(url_for('backup.index')) 