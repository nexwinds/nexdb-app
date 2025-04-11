"""
NEXDB - Project routes
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Project, DatabaseServer
from app.project.forms import ProjectForm, ProjectMemberForm
from app.project.utils import can_access_project, can_edit_project, can_delete_project
from sqlalchemy import or_

# Create Blueprint
project_bp = Blueprint('project', __name__)


@project_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard route."""
    # Get all projects the user has access to
    user_created_projects = Project.query.filter_by(created_by=current_user.id).all()
    user_member_projects = current_user.member_projects
    
    # Combine projects (removing duplicates)
    all_projects = list(set(user_created_projects + user_member_projects))
    
    # Get recent database servers
    recent_servers = DatabaseServer.query.join(Project).filter(
        or_(
            Project.created_by == current_user.id,
            Project.members.contains(current_user)
        )
    ).order_by(DatabaseServer.updated_at.desc()).limit(5).all()
    
    return render_template(
        'project/dashboard.html',
        title='Dashboard',
        projects=all_projects,
        recent_servers=recent_servers
    )


@project_bp.route('/projects')
@login_required
def index():
    """List all projects."""
    # Get all projects the user has access to
    user_created_projects = Project.query.filter_by(created_by=current_user.id).all()
    user_member_projects = current_user.member_projects
    
    # Combine projects (removing duplicates)
    all_projects = list(set(user_created_projects + user_member_projects))
    
    # Separate owned and shared projects
    owned_projects = user_created_projects
    shared_projects = [p for p in user_member_projects if p not in owned_projects]
    
    return render_template(
        'project/index.html',
        title='Projects',
        owned_projects=owned_projects,
        shared_projects=shared_projects
    )


@project_bp.route('/projects/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new project."""
    form = ProjectForm()
    
    if form.validate_on_submit():
        project = Project(
            name=form.name.data,
            description=form.description.data,
            created_by=current_user.id
        )
        
        db.session.add(project)
        db.session.commit()
        
        flash('Project created successfully.', 'success')
        return redirect(url_for('project.view', project_id=project.id))
    
    return render_template('project/create.html', title='Create Project', form=form)


@project_bp.route('/projects/<int:project_id>')
@login_required
def view(project_id):
    """View a project."""
    project = Project.query.get_or_404(project_id)
    
    # Check if user has access
    if not can_access_project(project, current_user):
        flash('You do not have access to this project.', 'danger')
        return redirect(url_for('project.index'))
    
    # Get database servers in the project
    servers = DatabaseServer.query.filter_by(project_id=project.id).all()
    
    # Check user's access level
    is_owner = project.created_by == current_user.id
    access_level = project.get_member_access_level(current_user.id) or 'owner' if is_owner else 'read'
    
    return render_template(
        'project/view.html',
        title=project.name,
        project=project,
        servers=servers,
        is_owner=is_owner,
        access_level=access_level
    )


@project_bp.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(project_id):
    """Edit a project."""
    project = Project.query.get_or_404(project_id)
    
    # Check if user has permission to edit
    if not can_edit_project(project, current_user):
        flash('You do not have permission to edit this project.', 'danger')
        return redirect(url_for('project.view', project_id=project.id))
    
    form = ProjectForm(obj=project)
    
    if form.validate_on_submit():
        project.name = form.name.data
        project.description = form.description.data
        
        db.session.commit()
        
        flash('Project updated successfully.', 'success')
        return redirect(url_for('project.view', project_id=project.id))
    
    return render_template('project/edit.html', title='Edit Project', form=form, project=project)


@project_bp.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def delete(project_id):
    """Delete a project."""
    project = Project.query.get_or_404(project_id)
    
    # Check if user has permission to delete
    if not can_delete_project(project, current_user):
        flash('You do not have permission to delete this project.', 'danger')
        return redirect(url_for('project.view', project_id=project.id))
    
    db.session.delete(project)
    db.session.commit()
    
    flash('Project deleted successfully.', 'success')
    return redirect(url_for('project.index'))


@project_bp.route('/projects/<int:project_id>/members', methods=['GET', 'POST'])
@login_required
def members(project_id):
    """Manage project members."""
    project = Project.query.get_or_404(project_id)
    
    # Check if user has permission to view/edit members
    if not can_edit_project(project, current_user):
        flash('You do not have permission to manage project members.', 'danger')
        return redirect(url_for('project.view', project_id=project.id))
    
    form = ProjectMemberForm()
    
    if form.validate_on_submit():
        from app.models import User
        
        # Find user by email
        user = User.query.filter_by(email=form.email.data).first()
        
        if not user:
            flash(f'User with email {form.email.data} not found.', 'danger')
        elif user.id == current_user.id:
            flash('You cannot add yourself as a member.', 'danger')
        elif user in project.members:
            flash(f'User {user.username} is already a member of this project.', 'danger')
        else:
            # Add user to project with selected access level
            project.add_member(user, form.access_level.data)
            db.session.commit()
            
            flash(f'User {user.username} added to project with {form.access_level.data} access.', 'success')
            return redirect(url_for('project.members', project_id=project.id))
    
    return render_template(
        'project/members.html',
        title='Project Members',
        project=project,
        form=form
    )


@project_bp.route('/projects/<int:project_id>/members/<int:user_id>/remove', methods=['POST'])
@login_required
def remove_member(project_id, user_id):
    """Remove a member from a project."""
    project = Project.query.get_or_404(project_id)
    
    # Check if user has permission to edit members
    if not can_edit_project(project, current_user):
        flash('You do not have permission to manage project members.', 'danger')
        return redirect(url_for('project.view', project_id=project.id))
    
    from app.models import User
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot remove yourself from the project.', 'danger')
    elif user not in project.members:
        flash(f'User {user.username} is not a member of this project.', 'danger')
    else:
        # Remove user from project
        project.remove_member(user)
        db.session.commit()
        
        flash(f'User {user.username} removed from project.', 'success')
    
    return redirect(url_for('project.members', project_id=project.id))


@project_bp.route('/projects/<int:project_id>/members/<int:user_id>/change-access', methods=['POST'])
@login_required
def change_member_access(project_id, user_id):
    """Change a member's access level."""
    project = Project.query.get_or_404(project_id)
    
    # Check if user has permission to edit members
    if not can_edit_project(project, current_user):
        flash('You do not have permission to manage project members.', 'danger')
        return redirect(url_for('project.view', project_id=project.id))
    
    from app.models import User
    
    user = User.query.get_or_404(user_id)
    access_level = request.form.get('access_level')
    
    if user.id == current_user.id:
        flash('You cannot change your own access level.', 'danger')
    elif user not in project.members:
        flash(f'User {user.username} is not a member of this project.', 'danger')
    elif access_level not in ['read', 'write', 'admin']:
        flash('Invalid access level.', 'danger')
    else:
        # Update user's access level
        project.add_member(user, access_level)
        db.session.commit()
        
        flash(f'User {user.username} access level changed to {access_level}.', 'success')
    
    return redirect(url_for('project.members', project_id=project.id)) 