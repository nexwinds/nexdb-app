#!/bin/bash

# Fix script for NEXDB routing issue
INSTALL_DIR="/opt/nexdb"
INIT_FILE="$INSTALL_DIR/app/__init__.py"

echo "🔧 Fixing NEXDB routing issue..."

# Backup the original __init__.py file
BACKUP_FILE="$INIT_FILE.bak.$(date +%s)"
echo "📑 Creating backup of original file at $BACKUP_FILE"
cp "$INIT_FILE" "$BACKUP_FILE"

# Update the index route to redirect to dashboard.index instead of health
echo "🔄 Updating the root route to redirect to the dashboard..."
sed -i 's/return redirect(url_for('\''health'\''))/return redirect(url_for('\''dashboard.index'\''))/' "$INIT_FILE"

# Verify the change was made
if grep -q "return redirect(url_for('dashboard.index'))" "$INIT_FILE"; then
    echo "✅ Route update successful!"
else
    echo "⚠️ Automatic replacement failed. Attempting manual file replacement..."
    
    # If sed fails, create a new file with the correct routing
    cat << EOF > "$INIT_FILE"
from flask import Flask, redirect, url_for, jsonify
from config import SECRET_KEY, HOST, PORT, ADMIN_USER, ADMIN_PASS
import os

def create_app():
    """Initialize the Flask application"""
    # Create Flask app
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nexdb.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
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
    
    # Root route
    @app.route('/')
    def index():
        return redirect(url_for('dashboard.index'))
    
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
    
    if [ $? -eq 0 ]; then
        echo "✅ Manual file replacement successful!"
    else
        echo "❌ Failed to update the file. Please check permissions and try again."
        echo "   You can manually edit $INIT_FILE and change the line:"
        echo "   'return redirect(url_for('health'))' to 'return redirect(url_for('dashboard.index'))'"
        exit 1
    fi
fi

# Restart service
echo "🔄 Restarting NEXDB service..."
systemctl restart nexdb

# Verify service is running
sleep 3
SERVICE_STATUS=$(systemctl is-active nexdb)
if [ "$SERVICE_STATUS" == "active" ]; then
    echo "✅ Service is now running! Status: $SERVICE_STATUS"
    
    # Check if the web service is responding
    echo "🔍 Verifying web service..."
    CURL_OUTPUT=$(curl -s -m 5 http://localhost:8080/health 2>&1)
    if [ $? -eq 0 ]; then
        echo "✅ Web service health check is responding!"
        IP=$(hostname -I | awk '{print $1}')
        echo -e "\n🎉 NEXDB should now be accessible at: http://$IP:8080"
        echo "   You should now be redirected to the dashboard login page instead of the health endpoint."
    else
        echo "⚠️ Web service is not responding on localhost:8080/health."
        echo "This may indicate another issue. Please check the logs:"
        echo "sudo journalctl -u nexdb --no-pager -n 20"
    fi
else
    echo "⚠️ Service is not running. Status: $SERVICE_STATUS"
    echo "Checking logs for more details..."
    journalctl -u nexdb --no-pager -n 20
fi

echo -e "\n📋 If issues persist, please check:"
echo "1. Application logs: sudo journalctl -u nexdb"
echo "2. File permissions: ls -la $INSTALL_DIR/app/"
echo "3. Routes registration: grep -r 'dashboard_bp' $INSTALL_DIR/app/" 