from flask import render_template, request, redirect, url_for, flash, session
from app.routes import auth_bp
from app.services.user_service import UserService
from functools import wraps
from config import SESSION_TIMEOUT
import datetime

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        # Check session timeout
        if SESSION_TIMEOUT:
            last_active = session.get('last_active')
            if last_active:
                last_active = datetime.datetime.fromisoformat(last_active)
                time_diff = datetime.datetime.now() - last_active
                if time_diff.total_seconds() > SESSION_TIMEOUT * 60:
                    session.clear()
                    flash('Your session has expired. Please log in again.', 'warning')
                    return redirect(url_for('auth.login'))
            
            # Update last active time
            session['last_active'] = datetime.datetime.now().isoformat()
            
        return f(*args, **kwargs)
    return decorated_function

# Admin access decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not session.get('is_admin', False):
            flash('Admin access required', 'danger')
            return redirect(url_for('dashboard.index'))
            
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required', 'danger')
            return render_template('auth/login.html')
        
        user = UserService.verify_password(username, password)
        
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['theme'] = user.theme_preference
            session['is_admin'] = user.is_admin
            session['last_active'] = datetime.datetime.now().isoformat()
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """User logout route"""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password route"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required', 'danger')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return render_template('auth/change_password.html')
        
        # Verify current password
        user = UserService.get_user_by_id(session['user_id'])
        if not user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return render_template('auth/change_password.html')
        
        # Change password
        UserService.change_password(session['user_id'], new_password)
        flash('Password changed successfully', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/change_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password route"""
    # TODO: Implement password reset functionality
    flash('Password reset functionality is not yet implemented', 'warning')
    return redirect(url_for('auth.login')) 