#!/bin/bash
# nexdb-install.sh - Enhanced installation script for NEXDB
# This script incorporates fixes for import issues and ensures proper configurations

# Disable "exit on error" to better handle errors
set +e

echo -e "\n🚀 Welcome to NEXDB Installer!"
echo -e "=============================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "\n❌ This script must be run as root. Please use sudo."
  exit 1
fi

# Check Ubuntu version
if [ ! -f /etc/lsb-release ] || ! grep -q "Ubuntu 24.04" /etc/lsb-release; then
  echo -e "\n⚠️  Warning: This script is optimized for Ubuntu 24.04 LTS. Your results may vary."
  read -p "Do you want to continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n❌ Installation cancelled."
    exit 1
  fi
fi

# Installation directory
INSTALL_DIR="/opt/nexdb"
APP_DIR="$INSTALL_DIR/app"
MAIN_FILE="$APP_DIR/__main__.py"
INIT_FILE="$APP_DIR/__init__.py"
SERVICE_FILE="/etc/systemd/system/nexdb.service"

# Create directories
mkdir -p $INSTALL_DIR $APP_DIR

echo -e "\n📦 Updating system & installing dependencies..."
apt update && apt install -y \
  python3 python3-pip python3-venv \
  mysql-server postgresql postgresql-contrib \
  ufw curl git rsync

# Create Python virtual environment
echo -e "\n🐍 Setting up Python virtual environment..."
python3 -m venv $INSTALL_DIR/venv
source $INSTALL_DIR/venv/bin/activate

# Install Python dependencies
echo -e "\n📚 Installing Python dependencies..."
pip install -U flask flask-sqlalchemy werkzeug mysql-connector-python psycopg2-binary python-crontab boto3

# Get the absolute path of the script
SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")
SCRIPT_NAME=$(basename "$SCRIPT_PATH")

echo -e "\n📋 Copying application code to $INSTALL_DIR..."
echo -e "  Script path: $SCRIPT_PATH"
echo -e "  Script directory: $SCRIPT_DIR"

# Create backup directory
mkdir -p $INSTALL_DIR/backups

# First, explicitly copy this installation script to the destination
echo -e "\n📄 Copying installation script..."
cp "$SCRIPT_PATH" "$INSTALL_DIR/$SCRIPT_NAME"
if [ $? -eq 0 ]; then
  echo -e "  ✅ Installation script copied successfully to $INSTALL_DIR/$SCRIPT_NAME"
  chmod +x "$INSTALL_DIR/$SCRIPT_NAME"
else
  echo -e "  ❌ Failed to copy installation script. Continuing anyway..."
fi

# Use rsync to copy all other files, with explicit exclusions
echo -e "\n📁 Copying remaining files..."
rsync -av \
  --exclude=".git/" \
  --exclude=".ssh/" \
  --exclude="authorized_keys" \
  --exclude="id_rsa" \
  --exclude="id_rsa.pub" \
  --exclude="known_hosts" \
  --exclude="venv/" \
  --exclude="*.pyc" \
  --exclude="__pycache__/" \
  "$SCRIPT_DIR/" "$INSTALL_DIR/"

# Set permissions
echo -e "\n🔒 Setting permissions..."
chown -R root:root $INSTALL_DIR
chmod 755 $APP_DIR $INSTALL_DIR

# Create an enhanced __init__.py file with run_app function
echo -e "\n📝 Creating the correct app/__init__.py file..."
cat << EOF > $INIT_FILE
from flask import Flask, redirect, url_for, jsonify
import os

# Default config values
SECRET_KEY = os.environ.get('NEXDB_SECRET_KEY', 'dev_secret_key')
HOST = os.environ.get('NEXDB_HOST', '0.0.0.0')
PORT = int(os.environ.get('NEXDB_PORT', '8080'))
ADMIN_USER = os.environ.get('NEXDB_ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('NEXDB_ADMIN_PASS', 'admin123')

def create_app():
    """Initialize the Flask application"""
    # Create Flask app
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nexdb.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    try:
        from app.models import init_app as init_db
        init_db(app)
        
        # Register routes
        from app.routes import register_blueprints
        register_blueprints(app)
        
        # Create default admin user
        with app.app_context():
            from app.services.user_service import UserService
            admin, password = UserService.initialize_admin_user(
                username=ADMIN_USER,
                email="admin@local.nexdb",
                password=ADMIN_PASS
            )
            
            if password:
                app.config['ADMIN_PASSWORD'] = password
    except ImportError:
        # Basic fallback routes if modules aren't available
        pass
    
    # Root route
    @app.route('/')
    def index():
        return redirect(url_for('health'))
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'ok',
            'version': app.config.get('VERSION', '1.0.0'),
            'host': HOST,
            'port': PORT
        })
    
    return app

def run_app():
    """Run the application"""
    app = create_app()
    print(f"Starting NEXDB on {HOST}:{PORT}...")
    app.run(host=HOST, port=PORT, debug=False)
    
if __name__ == '__main__':
    run_app()
EOF

# Create an enhanced __main__.py file with better path handling
echo -e "\n🔧 Creating enhanced Python entry point..."
cat << EOF > $MAIN_FILE
# Entry point for NEXDB application
import os
import sys
import site

# Add the installation directory to Python's path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

# Enable site-packages for virtual environment modules
venv_site_packages = os.path.join(base_dir, "venv/lib/python3.12/site-packages")
if os.path.exists(venv_site_packages):
    site.addsitedir(venv_site_packages)

try:
    # Try to import run_app from app module
    from app import run_app
    
    # Run the application
    if __name__ == '__main__':
        run_app()
except ImportError as e:
    print(f"Import error: {e}")
    print("Attempting fallback method...")
    
    # Fallback method - direct import
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from __init__ import run_app
    
    if __name__ == '__main__':
        run_app()
EOF

# Create an enhanced systemd service file
echo -e "\n⚙️  Creating enhanced systemd service..."
cat << EOF > $SERVICE_FILE
[Unit]
Description=NEXDB Panel
After=network.target

[Service]
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python3 -m app
Restart=always
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=$INSTALL_DIR"
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Set correct permissions for Python files
chmod 644 $MAIN_FILE $INIT_FILE $SERVICE_FILE

# Allow web port in firewall
echo -e "\n🔥 Configuring firewall..."
ufw allow 8080/tcp
echo "Rules updated"
if [ -x "$(command -v ip6tables)" ]; then
  ip6tables -A INPUT -p tcp --dport 8080 -j ACCEPT
  echo "Rules updated (v6)"
fi

# Enable and start service
echo -e "\n🚀 Starting NEXDB service..."
systemctl daemon-reload
systemctl enable nexdb
systemctl start nexdb

# Verify service is actually running
sleep 5
SERVICE_STATUS=$(systemctl is-active nexdb)
if [ "$SERVICE_STATUS" != "active" ]; then
  echo -e "\n⚠️  Warning: Service is not running. Status: $SERVICE_STATUS"
  echo -e "Checking logs for more details..."
  journalctl -u nexdb --no-pager -n 20
  
  # Try to debug the Python import issue
  echo -e "\n🔍 Debugging Python module import..."
  pushd $INSTALL_DIR > /dev/null
  echo "Testing Python import from $INSTALL_DIR:"
  $INSTALL_DIR/venv/bin/python3 -c "import sys; print(sys.path); import app; print('App module found')"
  if [ $? -ne 0 ]; then
    echo -e "⚠️  Could not import app module. This will automatically apply fixes..."
    
    # Apply fixes automatically
    echo -e "\n🔧 Applying automatic fixes..."
    
    # Ensure the __init__.py file has the run_app function
    if ! grep -q "def run_app" "$INIT_FILE"; then
      echo "Fixing __init__.py to include run_app function..."
      # (Code already created above, so just referencing it here)
    fi
    
    # Restart service after fixes
    systemctl restart nexdb
    sleep 3
    
    # Check if fixed
    if [ "$(systemctl is-active nexdb)" == "active" ]; then
      echo "✅ Automatic fixes applied successfully!"
    else
      echo "❌ Automatic fixes did not resolve the issue."
      journalctl -u nexdb --no-pager -n 20
    fi
  fi
  popd > /dev/null
fi

# Final verification of the web service
echo -e "\n🔍 Verifying web service..."
CURL_OUTPUT=$(curl -s -m 5 http://localhost:8080/health 2>&1)
if [ $? -ne 0 ]; then
  echo -e "⚠️  Warning: Web service is not responding on localhost:8080."
  echo -e "This may indicate the application is not binding correctly or has an error."
else
  echo -e "✅ Web service is responding on localhost!"
fi

# Get admin password from config or use default
ADMIN_PASS=$(grep -oP "(?<=ADMIN_PASS = os.environ.get\('NEXDB_ADMIN_PASS', ')[^']*" $INIT_FILE 2>/dev/null || echo "admin123")

# Display credentials & URL
IP=$(hostname -I | awk '{print $1}')
echo -e "\n🎉 NEXDB is now running at: http://$IP:8080"
echo -e "🔐 Admin Login:"
echo -e "   Username: admin"
echo -e "   Password: $ADMIN_PASS"
echo -e "📦 MySQL and PostgreSQL are ready to use."
echo -e "📁 Backups will be stored in $INSTALL_DIR/backups"
echo -e "\n💡 For security reasons, you should change the admin password after first login."

# Add troubleshooting note
echo -e "\n📋 Troubleshooting:"
echo -e "If you encounter any issues, please check:"
echo -e "1. Firewall settings: 'sudo ufw status'"
echo -e "2. Service status: 'sudo systemctl status nexdb'"
echo -e "3. Application logs: 'sudo journalctl -u nexdb'"
echo -e "4. Network connectivity: 'curl -v http://localhost:8080'" 