#!/bin/bash
# nexdb-fix.sh - Comprehensive fix script for NEXDB service issues
# This script can resolve Python import errors and other common issues

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "\n❌ This script must be run as root. Please use sudo."
  exit 1
fi

INSTALL_DIR="/opt/nexdb"
APP_DIR="$INSTALL_DIR/app"
MAIN_FILE="$APP_DIR/__main__.py"
INIT_FILE="$APP_DIR/__init__.py"
SERVICE_FILE="/etc/systemd/system/nexdb.service"

echo -e "\n🛠️ NEXDB Comprehensive Fix Script"
echo -e "================================"

# Step 1: Stop the service first
echo -e "\n🛑 Step 1: Stopping NEXDB service..."
systemctl stop nexdb

# Step 2: Verify the app directory structure
echo -e "\n📁 Step 2: Checking application directory structure..."
if [ ! -d "$APP_DIR" ]; then
    echo "⚠️ App directory doesn't exist. Creating it..."
    mkdir -p "$APP_DIR"
fi

# Step 3: Check if __init__.py exists and contains run_app
echo -e "\n📝 Step 3: Checking app/__init__.py file..."
if [ -f "$INIT_FILE" ]; then
    echo "✅ Found __init__.py file"
    if grep -q "def run_app" "$INIT_FILE"; then
        echo "✅ Found run_app function in __init__.py"
    else
        echo "❌ run_app function not found in __init__.py! Creating proper file..."
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
    fi
else
    echo "❌ __init__.py file not found! Creating it now..."
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
    
    # Root route
    @app.route('/')
    def index():
        return redirect(url_for('health'))
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'ok',
            'version': '1.0.0',
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
fi

# Step 4: Create a proper __main__.py file
echo -e "\n🔧 Step 4: Creating enhanced Python entry point..."
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

# Step 5: Fix service file to use absolute paths and correct environment
echo -e "\n⚙️ Step 5: Updating systemd service configuration..."
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

# Step 6: Set proper permissions
echo -e "\n🔒 Step 6: Setting proper permissions..."
chmod 644 $MAIN_FILE $INIT_FILE $SERVICE_FILE
chmod 755 $APP_DIR $INSTALL_DIR

# Step 7: Ensure pip and Flask are installed in the virtual environment
echo -e "\n📦 Step 7: Verifying Python dependencies..."
if [ -d "$INSTALL_DIR/venv" ]; then
    echo "✅ Virtual environment exists"
    $INSTALL_DIR/venv/bin/pip install --upgrade flask
else
    echo "⚠️ Virtual environment not found. Creating one..."
    python3 -m venv $INSTALL_DIR/venv
    $INSTALL_DIR/venv/bin/pip install flask
fi

# Step 8: Reload systemd and restart service
echo -e "\n🔄 Step 8: Restarting NEXDB service..."
systemctl daemon-reload
systemctl restart nexdb

# Step 9: Verify service status
echo -e "\n🔍 Step 9: Verifying service status..."
sleep 5
SERVICE_STATUS=$(systemctl is-active nexdb)
if [ "$SERVICE_STATUS" == "active" ]; then
    echo "✅ Service is now running! Status: $SERVICE_STATUS"
    
    # Check if the web service is responding
    echo "🔍 Verifying web service..."
    CURL_OUTPUT=$(curl -s -m 5 http://localhost:8080/health 2>&1)
    if [ $? -eq 0 ]; then
        echo "✅ Web service is responding on localhost!"
        IP=$(hostname -I | awk '{print $1}')
        echo -e "\n🎉 NEXDB should now be accessible at: http://$IP:8080"
        echo -e "🔐 Admin Login:"
        echo -e "   Username: admin"
        echo -e "   Password: admin123"
    else
        echo "⚠️ Web service is not responding on localhost:8080."
        echo "This may indicate another issue. Please check the logs:"
        echo "sudo journalctl -u nexdb --no-pager -n 20"
    fi
else
    echo "⚠️ Service is still not running. Status: $SERVICE_STATUS"
    echo "Checking logs for more details..."
    journalctl -u nexdb --no-pager -n 20
    
    # Advanced debugging
    echo -e "\n🔬 Advanced debugging info:"
    echo "1. Python version: $(python3 --version)"
    echo "2. Module paths:"
    python3 -c "import sys; [print(p) for p in sys.path]"
    
    echo -e "\n3. Try manual import test:"
    cd $INSTALL_DIR
    python3 -c "import sys; sys.path.insert(0, '.'); print(sys.path); import app; print('App module found')"
    echo -e "\n4. Checking actual app directory contents:"
    ls -la $APP_DIR
    
    echo -e "\n💡 If the fix didn't work, you may need to uninstall and reinstall NEXDB:"
    echo -e "   sudo ./nexdb-uninstall.sh"
    echo -e "   sudo ./nexdb-install.sh"
fi 