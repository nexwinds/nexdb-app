"""
NEXDB - Authentication utilities
"""

import jwt
from time import time
from flask import current_app, render_template, url_for
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

def generate_reset_token(email, expires_in=3600):
    """Generate a JWT token for password reset."""
    return jwt.encode(
        {'reset_password': email, 'exp': time() + expires_in},
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def verify_reset_token(token):
    """Verify a password reset token."""
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return data.get('reset_password')
    except Exception as e:
        logging.error(f"Token verification error: {e}")
        return None

def send_password_reset_email(user, token):
    """Send password reset email."""
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    # In a real application, you would configure an email service
    # This is a placeholder implementation
    try:
        # Create message content
        html_body = render_template('email/reset_password.html', 
                                   user=user, 
                                   reset_url=reset_url)
        text_body = render_template('email/reset_password.txt', 
                                   user=user, 
                                   reset_url=reset_url)
        
        # For now, we'll just log the reset URL
        logging.info(f"Password reset URL for {user.email}: {reset_url}")
        
        # In production, you would send a real email:
        # send_email(subject="Reset Your Password",
        #            recipients=[user.email],
        #            text_body=text_body,
        #            html_body=html_body)
        
        return True
    except Exception as e:
        logging.error(f"Failed to send password reset email: {e}")
        return False

def send_email(subject, recipients, text_body, html_body):
    """Send an email using SMTP."""
    # This is a simple email sending function
    # In production, you would use a service like SendGrid, Mailgun, etc.
    
    # Sample implementation for reference
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@nexdb.example.com')
        msg['To'] = ', '.join(recipients)
        
        # Attach parts
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Create SMTP connection
        smtp_server = current_app.config.get('MAIL_SERVER', 'localhost')
        smtp_port = current_app.config.get('MAIL_PORT', 25)
        smtp_username = current_app.config.get('MAIL_USERNAME')
        smtp_password = current_app.config.get('MAIL_PASSWORD')
        use_tls = current_app.config.get('MAIL_USE_TLS', False)
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls()
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        logging.error(f"Email sending error: {e}")
        return False 