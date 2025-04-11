from app.models import db
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import os
import hashlib
from datetime import datetime

class User:
    """Simple user model"""
    def __init__(self, id, username, email, password_hash, is_admin=False, created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.created_at = created_at or datetime.now()

class UserService:
    """Service for user management"""
    # In-memory user storage (for development/fallback)
    _users = []
    _admin_initialized = False
    
    @classmethod
    def initialize_admin_user(cls, username, email, password):
        """Initialize the admin user if not exists"""
        if cls._admin_initialized:
            return None, None
            
        # Check if we have any users first
        if not cls._users:
            # Hash the password
            salt = secrets.token_hex(8)
            password_hash = cls._hash_password(password, salt)
            
            # Create admin user
            admin_user = User(
                id=1,
                username=username,
                email=email,
                password_hash=f"{salt}${password_hash}",
                is_admin=True,
                created_at=datetime.now()
            )
            
            # Add to in-memory storage
            cls._users.append(admin_user)
            cls._admin_initialized = True
            
            return admin_user, password
        
        return None, None
    
    @staticmethod
    def _hash_password(password, salt):
        """Hash a password with the provided salt"""
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    @classmethod
    def authenticate(cls, username, password):
        """Authenticate a user by username and password"""
        user = cls.get_by_username(username)
        if not user:
            return None
            
        # Check password
        salt, hashed = user.password_hash.split('$', 1)
        if cls._hash_password(password, salt) == hashed:
            return user
        
        return None
    
    @classmethod
    def get_by_username(cls, username):
        """Get a user by username"""
        for user in cls._users:
            if user.username == username:
                return user
        return None
    
    @classmethod
    def get_by_id(cls, user_id):
        """Get a user by ID"""
        for user in cls._users:
            if user.id == user_id:
                return user
        return None
    
    @classmethod
    def create_user(cls, username, email, password, is_admin=False):
        """Create a new user"""
        # Check if username already exists
        if cls.get_by_username(username):
            return None
            
        # Generate a new salt and hash the password
        salt = secrets.token_hex(8)
        password_hash = cls._hash_password(password, salt)
        
        # Create new user with the next available ID
        next_id = max([user.id for user in cls._users], default=0) + 1
        new_user = User(
            id=next_id,
            username=username,
            email=email,
            password_hash=f"{salt}${password_hash}",
            is_admin=is_admin,
            created_at=datetime.now()
        )
        
        # Add to in-memory storage
        cls._users.append(new_user)
        
        return new_user
    
    @classmethod
    def get_all_users(cls):
        """Get all users"""
        return cls._users
    
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
    def delete_user(user_id):
        """Delete a user"""
        user = UserService.get_user_by_id(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False 