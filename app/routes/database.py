from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.routes import database_bp
from app.routes.auth import login_required, admin_required
from app.services.db_service import DBService
import secrets

@database_bp.route('/')
@login_required
def index():
    """Database management overview page"""
    mysql_dbs = DBService.get_mysql_databases()
    postgres_dbs = DBService.get_postgres_databases()
    credentials = DBService.get_all_credentials()
    
    return render_template('database/index.html',
                           mysql_dbs=mysql_dbs,
                           postgres_dbs=postgres_dbs,
                           credentials=credentials,
                           theme=session.get('theme', 'light'))

@database_bp.route('/create-db', methods=['GET', 'POST'])
@login_required
def create_database():
    """Create a new database"""
    if request.method == 'POST':
        db_type = request.form.get('db_type')
        db_name = request.form.get('db_name')
        
        if not db_type or not db_name:
            flash('Database type and name are required', 'danger')
            return redirect(url_for('database.create_database'))
        
        result = False
        if db_type == 'mysql':
            result = DBService.create_mysql_database(db_name)
        elif db_type == 'postgres':
            result = DBService.create_postgres_database(db_name)
        
        if result:
            flash(f'{db_type.upper()} database "{db_name}" created successfully', 'success')
            return redirect(url_for('database.index'))
        else:
            flash(f'Failed to create {db_type.upper()} database', 'danger')
    
    return render_template('database/create_db.html', theme=session.get('theme', 'light'))

@database_bp.route('/create-user', methods=['GET', 'POST'])
@login_required
def create_user():
    """Create a new database user"""
    if request.method == 'POST':
        db_type = request.form.get('db_type')
        username = request.form.get('username')
        password = request.form.get('password')
        db_name = request.form.get('db_name') or None
        
        # Generate a password if not provided
        if not password:
            password = secrets.token_urlsafe(12)
        
        if not db_type or not username:
            flash('Database type and username are required', 'danger')
            return render_template('database/create_user.html', 
                                  mysql_dbs=DBService.get_mysql_databases(),
                                  postgres_dbs=DBService.get_postgres_databases(),
                                  theme=session.get('theme', 'light'))
        
        result = False
        if db_type == 'mysql':
            result = DBService.create_mysql_user(
                username=username,
                password=password,
                db_name=db_name,
                user_id=session.get('user_id')
            )
        elif db_type == 'postgres':
            result = DBService.create_postgres_user(
                username=username,
                password=password,
                db_name=db_name,
                user_id=session.get('user_id')
            )
        
        if result:
            flash(f'{db_type.upper()} user "{username}" created successfully', 'success')
            if not request.form.get('password'):
                flash(f'Generated password: {password}', 'info')
            return redirect(url_for('database.index'))
        else:
            flash(f'Failed to create {db_type.upper()} user', 'danger')
    
    return render_template('database/create_user.html',
                          mysql_dbs=DBService.get_mysql_databases(),
                          postgres_dbs=DBService.get_postgres_databases(),
                          theme=session.get('theme', 'light'))

@database_bp.route('/open-port/<db_type>')
@admin_required
def open_port(db_type):
    """Open database port in firewall"""
    if db_type not in ['mysql', 'postgres']:
        flash('Invalid database type', 'danger')
        return redirect(url_for('database.index'))
    
    result = DBService.open_port(db_type)
    
    if result:
        port = '3306' if db_type == 'mysql' else '5432'
        flash(f'Port {port} opened for {db_type.upper()} successfully', 'success')
    else:
        flash(f'Failed to open port for {db_type.upper()}', 'danger')
    
    return redirect(url_for('database.index'))

@database_bp.route('/view-credentials/<int:credential_id>')
@login_required
def view_credentials(credential_id):
    """View database credentials"""
    credential = DBService.get_credential_by_id(credential_id)
    
    if not credential:
        flash('Credential not found', 'danger')
        return redirect(url_for('database.index'))
    
    return render_template('database/view_credentials.html',
                          credential=credential,
                          theme=session.get('theme', 'light')) 