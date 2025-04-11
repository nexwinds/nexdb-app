from app.models import db
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

class UserService:
    @staticmethod
    def create_user(username, email, password, is_admin=False, theme_preference='light'):
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                return None
            
            # Create new user
            user = User(
                username=username,
                email=email,
                password=password,
                is_admin=is_admin,
                theme_preference=theme_preference
            )
            
            db.session.add(user)
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user: {str(e)}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get a user by ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_username(username):
        """Get a user by username"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def verify_password(username, password):
        """Verify a user's password"""
        user = UserService.get_user_by_username(username)
        if user and user.check_password(password):
            return user
        return None
    
    @staticmethod
    def change_password(user_id, new_password):
        """Change a user's password"""
        user = UserService.get_user_by_id(user_id)
        if user:
            user.set_password(new_password)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def update_theme_preference(user_id, theme):
        """Update a user's theme preference"""
        user = UserService.get_user_by_id(user_id)
        if user and theme in ['light', 'dark']:
            user.theme_preference = theme
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_all_users():
        """Get all users"""
        return User.query.all()
    
    @staticmethod
    def delete_user(user_id):
        """Delete a user"""
        user = UserService.get_user_by_id(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def initialize_admin_user(username, email, password=None):
        """Initialize the admin user if it doesn't exist"""
        # Check if admin user exists
        admin = User.query.filter_by(is_admin=True).first()
        
        if not admin:
            # Generate a random password if none provided
            if not password:
                password = secrets.token_urlsafe(12)
            
            # Create admin user
            admin = UserService.create_user(
                username=username,
                email=email,
                password=password,
                is_admin=True
            )
            
            return admin, password
        
        return admin, None 