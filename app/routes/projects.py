from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.routes import projects_bp
from app.routes.auth import login_required
from app.services.db_service import DBService

@projects_bp.route('/')
@login_required
def index():
    """Projects management overview page"""
    # For now just pass database lists to the template
    # In a real implementation, we would also fetch projects from a database
    
    mysql_dbs = DBService.get_mysql_databases()
    postgres_dbs = DBService.get_postgres_databases()
    
    return render_template('projects/index.html',
                          mysql_dbs=mysql_dbs,
                          postgres_dbs=postgres_dbs,
                          theme=session.get('theme', 'light'))

@projects_bp.route('/create', methods=['POST'])
@login_required
def create_project():
    """Create a new project"""
    # This would normally save the project to a database
    # For now, just return a success message
    
    if request.method == 'POST':
        project_name = request.form.get('project_name')
        project_description = request.form.get('project_description')
        mysql_databases = request.form.getlist('mysql_databases')
        postgres_databases = request.form.getlist('postgres_databases')
        
        # Validate input
        if not project_name:
            flash('Project name is required', 'danger')
            return redirect(url_for('projects.index'))
        
        # In a real implementation, we would create the project in the database
        flash(f'Project "{project_name}" created successfully', 'success')
        
        # For API requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'Project "{project_name}" created successfully'
            })
            
        return redirect(url_for('projects.index'))
    
    return redirect(url_for('projects.index'))

@projects_bp.route('/<int:project_id>')
@login_required
def view_project(project_id):
    """View a single project"""
    # This would normally fetch the project from a database
    # For now, just return a placeholder template
    
    return render_template('projects/view.html',
                          project_id=project_id,
                          theme=session.get('theme', 'light'))

@projects_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    """Edit a project"""
    # This would normally fetch and update the project in a database
    
    if request.method == 'POST':
        project_name = request.form.get('project_name')
        project_description = request.form.get('project_description')
        mysql_databases = request.form.getlist('mysql_databases')
        postgres_databases = request.form.getlist('postgres_databases')
        
        # Validate input
        if not project_name:
            flash('Project name is required', 'danger')
            return redirect(url_for('projects.edit_project', project_id=project_id))
        
        # In a real implementation, we would update the project in the database
        flash(f'Project "{project_name}" updated successfully', 'success')
        return redirect(url_for('projects.view_project', project_id=project_id))
    
    # For GET requests, render the edit form
    # In a real implementation, we would fetch the project from the database
    mysql_dbs = DBService.get_mysql_databases()
    postgres_dbs = DBService.get_postgres_databases()
    
    # Placeholder project data
    project = {
        'id': project_id,
        'name': 'Project Name',
        'description': 'Project Description',
        'mysql_databases': [],
        'postgres_databases': []
    }
    
    return render_template('projects/edit.html',
                          project=project,
                          mysql_dbs=mysql_dbs,
                          postgres_dbs=postgres_dbs,
                          theme=session.get('theme', 'light'))

@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    """Delete a project"""
    # This would normally delete the project from a database
    
    # In a real implementation, we would delete the project from the database
    flash('Project deleted successfully', 'success')
    
    # For API requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': 'Project deleted successfully'
        })
        
    return redirect(url_for('projects.index')) 