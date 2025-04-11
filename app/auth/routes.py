"""
NEXDB - Authentication routes
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app import db, limiter
from app.models import User
from app.auth.forms import LoginForm, RegistrationForm, PasswordResetRequestForm, PasswordResetForm
from app.auth.utils import send_password_reset_email, generate_reset_token, verify_reset_token
from datetime import datetime

# Create Blueprint
auth_bp = Blueprint('auth', __name__)

# Rate limiting for sensitive routes
@auth_bp.before_request
def update_last_seen():
    if current_user.is_authenticated:
        current_user.last_login_at = datetime.utcnow()
        db.session.commit()


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    """User login route."""
    if current_user.is_authenticated:
        return redirect(url_for('project.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            if not user.active:
                flash('This account has been deactivated.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('project.dashboard')
            return redirect(next_page)
        flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html', title='Sign In', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout route."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def register():
    """User registration route."""
    if current_user.is_authenticated:
        return redirect(url_for('project.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            active=True
        )
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)


@auth_bp.route('/reset-password-request', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def reset_password_request():
    """Request password reset route."""
    if current_user.is_authenticated:
        return redirect(url_for('project.dashboard'))
    
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = generate_reset_token(user.email)
            send_password_reset_email(user, token)
        # Always show success message, even if email doesn't exist (for security)
        flash('Check your email for password reset instructions.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token route."""
    if current_user.is_authenticated:
        return redirect(url_for('project.dashboard'))
    
    email = verify_reset_token(token)
    if not email:
        flash('Invalid or expired reset token.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = form.password.data
            db.session.commit()
            flash('Your password has been reset!', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', title='Reset Password', form=form)


@auth_bp.route('/profile')
@login_required
def profile():
    """User profile route."""
    return render_template('auth/profile.html', title='Profile', user=current_user) 