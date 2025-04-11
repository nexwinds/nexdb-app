import os
import secrets

# Application Settings
APP_NAME = "NEXDB"
APP_VERSION = "1.0.0"
SECRET_KEY = secrets.token_hex(16)

# Server Settings
HOST = "0.0.0.0"
PORT = 8080

# Database Settings
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# User Settings
ADMIN_USER = "admin"
ADMIN_PASS = os.environ.get("NEXDB_ADMIN_PASS", secrets.token_urlsafe(12))

# Theme Settings
DEFAULT_THEME = "light"

# Security Settings
SESSION_TIMEOUT = 30  # minutes

# S3 Backup Settings
S3_ENABLED = False
S3_BUCKET = ""
S3_ACCESS_KEY = ""
S3_SECRET_KEY = ""
S3_REGION = "" 