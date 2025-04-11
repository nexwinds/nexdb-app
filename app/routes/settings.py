from flask import render_template, request, redirect, url_for, flash, session
from app.routes import settings_bp
from app.routes.auth import admin_required
import os
import json

@settings_bp.route('/')
@admin_required
def index():
    """Settings overview page"""
    # Get S3 settings
    s3_enabled = os.environ.get('NEXDB_S3_ENABLED', 'False').lower() == 'true'
    s3_bucket = os.environ.get('NEXDB_S3_BUCKET', '')
    s3_region = os.environ.get('NEXDB_S3_REGION', '')
    
    # Get backup settings
    backup_dir = os.environ.get('NEXDB_BACKUP_DIR', '/opt/nexdb/backups')
    
    # Get security settings
    session_timeout = int(os.environ.get('NEXDB_SESSION_TIMEOUT', '30'))
    
    return render_template('settings/index.html',
                          s3_enabled=s3_enabled,
                          s3_bucket=s3_bucket,
                          s3_region=s3_region,
                          backup_dir=backup_dir,
                          session_timeout=session_timeout,
                          theme=session.get('theme', 'light'))

@settings_bp.route('/s3', methods=['GET', 'POST'])
@admin_required
def s3_settings():
    """S3 backup settings"""
    if request.method == 'POST':
        s3_enabled = 'enabled' in request.form
        s3_bucket = request.form.get('bucket', '')
        s3_region = request.form.get('region', '')
        s3_access_key = request.form.get('access_key', '')
        s3_secret_key = request.form.get('secret_key', '')
        
        # Update environment variables
        os.environ['NEXDB_S3_ENABLED'] = str(s3_enabled)
        os.environ['NEXDB_S3_BUCKET'] = s3_bucket
        os.environ['NEXDB_S3_REGION'] = s3_region
        
        # Only update keys if provided (for security)
        if s3_access_key:
            os.environ['NEXDB_S3_ACCESS_KEY'] = s3_access_key
        if s3_secret_key:
            os.environ['NEXDB_S3_SECRET_KEY'] = s3_secret_key
        
        # Save to config file
        try:
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
            config_file = os.path.join(config_dir, "s3_config.json")
            
            config = {
                'enabled': s3_enabled,
                'bucket': s3_bucket,
                'region': s3_region
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            flash('S3 settings updated successfully', 'success')
        except Exception as e:
            flash(f'Error saving S3 settings: {str(e)}', 'danger')
        
        return redirect(url_for('settings.index'))
    
    # Current settings
    s3_enabled = os.environ.get('NEXDB_S3_ENABLED', 'False').lower() == 'true'
    s3_bucket = os.environ.get('NEXDB_S3_BUCKET', '')
    s3_region = os.environ.get('NEXDB_S3_REGION', '')
    s3_access_key = os.environ.get('NEXDB_S3_ACCESS_KEY', '')
    
    return render_template('settings/s3.html',
                          s3_enabled=s3_enabled,
                          s3_bucket=s3_bucket,
                          s3_region=s3_region,
                          s3_access_key=s3_access_key,
                          theme=session.get('theme', 'light'))

@settings_bp.route('/backup', methods=['GET', 'POST'])
@admin_required
def backup_settings():
    """Backup settings"""
    if request.method == 'POST':
        backup_dir = request.form.get('backup_dir', '/opt/nexdb/backups')
        
        # Update environment variables
        os.environ['NEXDB_BACKUP_DIR'] = backup_dir
        
        # Create the directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        # Save to config file
        try:
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
            config_file = os.path.join(config_dir, "backup_config.json")
            
            config = {
                'backup_dir': backup_dir
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            flash('Backup settings updated successfully', 'success')
        except Exception as e:
            flash(f'Error saving backup settings: {str(e)}', 'danger')
        
        return redirect(url_for('settings.index'))
    
    # Current settings
    backup_dir = os.environ.get('NEXDB_BACKUP_DIR', '/opt/nexdb/backups')
    
    return render_template('settings/backup.html',
                          backup_dir=backup_dir,
                          theme=session.get('theme', 'light'))

@settings_bp.route('/security', methods=['GET', 'POST'])
@admin_required
def security_settings():
    """Security settings"""
    if request.method == 'POST':
        session_timeout = int(request.form.get('session_timeout', 30))
        
        # Update environment variables
        os.environ['NEXDB_SESSION_TIMEOUT'] = str(session_timeout)
        
        # Save to config file
        try:
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
            config_file = os.path.join(config_dir, "security_config.json")
            
            config = {
                'session_timeout': session_timeout
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            flash('Security settings updated successfully', 'success')
        except Exception as e:
            flash(f'Error saving security settings: {str(e)}', 'danger')
        
        return redirect(url_for('settings.index'))
    
    # Current settings
    session_timeout = int(os.environ.get('NEXDB_SESSION_TIMEOUT', '30'))
    
    return render_template('settings/security.html',
                          session_timeout=session_timeout,
                          theme=session.get('theme', 'light')) 