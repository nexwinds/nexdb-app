from flask import render_template, request, redirect, url_for, flash, session
from app.routes import user_bp
from app.routes.auth import login_required, admin_required
from app.services.user_service import UserService
import secrets

@user_bp.route('/')
@admin_required
def index():
    """User management overview page"""
    users = UserService.get_all_users()
    return render_template('user/index.html', 
                          users=users,
                          theme=session.get('theme', 'light'))

@user_bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create_user():
    """Create a new application user"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = 'is_admin' in request.form
        theme_preference = request.form.get('theme_preference', 'light')
        
        # Generate a password if not provided
        if not password:
            password = secrets.token_urlsafe(12)
        
        if not username or not email:
            flash('Username and email are required', 'danger')
            return render_template('user/create.html', theme=session.get('theme', 'light'))
        
        user = UserService.create_user(
            username=username,
            email=email,
            password=password,
            is_admin=is_admin,
            theme_preference=theme_preference
        )
        
        if user:
            flash(f'User "{username}" created successfully', 'success')
            if not request.form.get('password'):
                flash(f'Generated password: {password}', 'info')
            return redirect(url_for('user.index'))
        else:
            flash('Failed to create user. Username or email may already exist.', 'danger')
    
    return render_template('user/create.html', theme=session.get('theme', 'light'))

@user_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit an existing user"""
    user = UserService.get_user_by_id(user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('user.index'))
    
    if request.method == 'POST':
        # Only admins can change admin status
        is_admin = 'is_admin' in request.form
        theme_preference = request.form.get('theme_preference')
        
        # Update user
        user.is_admin = is_admin
        if theme_preference:
            user.theme_preference = theme_preference
        
        # Handle password change
        new_password = request.form.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        try:
            from app.models import db
            db.session.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('user.index'))
        except Exception as e:
            flash(f'Error updating user: {str(e)}', 'danger')
    
    return render_template('user/edit.html', user=user, theme=session.get('theme', 'light'))

@user_bp.route('/delete/<int:user_id>')
@admin_required
def delete_user(user_id):
    """Delete a user"""
    # Prevent deleting yourself
    if user_id == session.get('user_id'):
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('user.index'))
    
    result = UserService.delete_user(user_id)
    
    if result:
        flash('User deleted successfully', 'success')
    else:
        flash('Failed to delete user', 'danger')
    
    return redirect(url_for('user.index'))

@user_bp.route('/profile')
@login_required
def profile():
    """View user profile"""
    user = UserService.get_user_by_id(session.get('user_id'))
    return render_template('user/profile.html', user=user, theme=session.get('theme', 'light'))

@user_bp.route('/toggle-theme')
@login_required
def toggle_theme():
    """Toggle user theme preference"""
    user_id = session.get('user_id')
    current_theme = session.get('theme', 'light')
    new_theme = 'dark' if current_theme == 'light' else 'light'
    
    result = UserService.update_theme_preference(user_id, new_theme)
    
    if result:
        session['theme'] = new_theme
        flash(f'Theme changed to {new_theme}', 'success')
    else:
        flash('Failed to change theme', 'danger')
    
    # Redirect back to the previous page
    return redirect(request.referrer or url_for('dashboard.index')) 