"""
NEXDB - Configuration settings
"""

import os
import secrets
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory of the application
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    """Base configuration."""
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    DEBUG = False
    TESTING = False
    
    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Security settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True  # Should be True in production
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True  # Should be True in production
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    
    # Backup settings
    S3_BUCKET = os.getenv('S3_BUCKET', '')
    S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY', '')
    S3_SECRET_KEY = os.getenv('S3_SECRET_KEY', '')
    S3_REGION = os.getenv('S3_REGION', 'us-east-1')
    
    # Database credentials storage (encrypted in the database)
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', secrets.token_hex(16))
    
    # MySQL default settings
    MYSQL_DEFAULT_HOST = os.getenv('MYSQL_DEFAULT_HOST', 'localhost')
    MYSQL_DEFAULT_PORT = os.getenv('MYSQL_DEFAULT_PORT', 3306)
    
    # PostgreSQL default settings
    POSTGRES_DEFAULT_HOST = os.getenv('POSTGRES_DEFAULT_HOST', 'localhost')
    POSTGRES_DEFAULT_PORT = os.getenv('POSTGRES_DEFAULT_PORT', 5432)
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_HEADERS_ENABLED = True
    
    # APScheduler settings
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "UTC"


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL',
                                        f'sqlite:///{os.path.join(basedir, "dev.sqlite")}')
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL',
                                        f'sqlite:///{os.path.join(basedir, "test.sqlite")}')
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',
                                        f'sqlite:///{os.path.join(basedir, "app.sqlite")}')
    SERVER_NAME = os.getenv('SERVER_NAME')
    PREFERRED_URL_SCHEME = 'https'


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 