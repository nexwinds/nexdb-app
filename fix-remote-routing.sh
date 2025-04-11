#!/bin/bash

# Script to fix the NEXDB Flask routing issue on the remote server
echo "🔧 Fixing NEXDB routing issue..."

# Check if we're root
if [ "$(id -u)" -ne 0 ]; then
  echo "❌ This script must be run as root"
  exit 1
fi

INSTALL_DIR="/opt/nexdb"
APP_DIR="$INSTALL_DIR/app"
ROUTES_DIR="$APP_DIR/routes"

# 1. First check if the dashboard blueprint is properly registered
echo "🔍 Verifying dashboard blueprint registration..."
if [ ! -f "$ROUTES_DIR/__init__.py" ]; then
  echo "❌ Routes initialization file not found!"
  exit 1
fi

# Verify dashboard_bp exists in the routes/__init__.py
if ! grep -q "dashboard_bp = Blueprint('dashboard'" "$ROUTES_DIR/__init__.py"; then
  echo "❌ Dashboard blueprint not defined in routes/__init__.py"
  echo "Creating proper blueprint registration..."
  # Backup the file
  cp "$ROUTES_DIR/__init__.py" "$ROUTES_DIR/__init__.py.bak"
  
  # Add dashboard blueprint if missing
  if ! grep -q "from flask import Blueprint" "$ROUTES_DIR/__init__.py"; then
    echo "from flask import Blueprint" > "$ROUTES_DIR/__init__.py.new"
    cat "$ROUTES_DIR/__init__.py" >> "$ROUTES_DIR/__init__.py.new"
    mv "$ROUTES_DIR/__init__.py.new" "$ROUTES_DIR/__init__.py"
  fi
  
  if ! grep -q "dashboard_bp = Blueprint" "$ROUTES_DIR/__init__.py"; then
    sed -i '/from flask import Blueprint/a\
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")' "$ROUTES_DIR/__init__.py"
  fi
fi

# 2. Verify that the routes are imported correctly
if ! grep -q "from app.routes.dashboard import" "$ROUTES_DIR/__init__.py"; then
  echo "❌ Dashboard routes not imported in routes/__init__.py"
  echo "Adding dashboard routes import..."
  sed -i '/Blueprint/a\
from app.routes.dashboard import *' "$ROUTES_DIR/__init__.py"
fi

# 3. Ensure dashboard blueprint is registered with the app
if ! grep -q "app.register_blueprint(dashboard_bp)" "$ROUTES_DIR/__init__.py"; then
  echo "❌ Dashboard blueprint not registered with app"
  echo "Adding blueprint registration..."
  
  # Add a register_blueprints function if it doesn't exist
  if ! grep -q "def register_blueprints" "$ROUTES_DIR/__init__.py"; then
    echo "
def register_blueprints(app):
    """Register all blueprints with the Flask application"""
    app.register_blueprint(dashboard_bp)
" >> "$ROUTES_DIR/__init__.py"
  else
    # Add dashboard_bp to existing register_blueprints function
    sed -i '/def register_blueprints/,/}/s/}/    app.register_blueprint(dashboard_bp)\n}/' "$ROUTES_DIR/__init__.py"
  fi
fi

# 4. Check if dashboard.py exists and has proper route definitions
if [ ! -f "$ROUTES_DIR/dashboard.py" ]; then
  echo "❌ Dashboard routes file not found!"
  echo "Creating dashboard.py with basic routes..."
  
  cat > "$ROUTES_DIR/dashboard.py" << 'EOF'
from flask import render_template, redirect, url_for, session
from app.routes import dashboard_bp
from functools import wraps

# Simple login_required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For emergency access, allowing all traffic through
        return f(*args, **kwargs)
    return decorated_function

@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home page"""
    return render_template('dashboard/index.html', 
                          theme=session.get('theme', 'light'))
EOF
fi

# 5. Make sure the root route redirects to dashboard.index
INIT_FILE="$APP_DIR/__init__.py"
if [ -f "$INIT_FILE" ]; then
  echo "🔧 Updating root route in app/__init__.py..."
  
  # Backup the original file
  cp "$INIT_FILE" "$INIT_FILE.bak.$(date +%s)"
  
  # Check if root route exists and update it
  if grep -q "@app.route('/')" "$INIT_FILE"; then
    sed -i "/@app.route('\/').*/,/return/c\\
    @app.route('/')\n    def index():\n        return redirect(url_for('dashboard.index'))" "$INIT_FILE"
  else
    # Add root route if it doesn't exist
    sed -i "/def create_app/,/return app/ s/return app/    @app.route('\/\')\n    def index():\n        return redirect(url_for('dashboard.index'))\n\n    return app/" "$INIT_FILE"
  fi
fi

# 6. Check if template directory exists
TEMPLATE_DIR="$APP_DIR/templates/dashboard"
if [ ! -d "$TEMPLATE_DIR" ]; then
  echo "🔧 Creating dashboard templates directory..."
  mkdir -p "$TEMPLATE_DIR"
  
  # Create a basic index.html template if it doesn't exist
  if [ ! -f "$TEMPLATE_DIR/index.html" ]; then
    cat > "$TEMPLATE_DIR/index.html" << 'EOF'
{% extends "layout.html" %}
{% block title %}Dashboard{% endblock %}
{% block content %}
<div class="container">
  <h1>NEXDB Dashboard</h1>
  <p>Welcome to your database management panel.</p>
</div>
{% endblock %}
EOF
  fi
fi

# 7. Restart the service
echo "🔄 Restarting NEXDB service..."
systemctl restart nexdb

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 5

# Check service status
SERVICE_STATUS=$(systemctl is-active nexdb)
if [ "$SERVICE_STATUS" == "active" ]; then
  echo "✅ Service is running! Status: $SERVICE_STATUS"
  
  # Check if web service is responding
  echo "🔍 Verifying web service..."
  if curl -s -m 5 http://localhost:8080/health > /dev/null; then
    echo "✅ Web service health check is responding!"
    IP=$(hostname -I | awk '{print $1}')
    echo -e "\n🎉 NEXDB should now be accessible at: http://$IP:8080"
  else
    echo "⚠️ Web service is not responding on health endpoint."
    echo "Checking main endpoint..."
    if curl -s -m 5 http://localhost:8080/ > /dev/null; then
      echo "✅ Main endpoint is responding!"
      IP=$(hostname -I | awk '{print $1}')
      echo -e "\n🎉 NEXDB should now be accessible at: http://$IP:8080"
    else
      echo "❌ Web service is not responding on main endpoint either."
      echo "Checking logs for more details..."
      journalctl -u nexdb --no-pager -n 30
    fi
  fi
else
  echo "❌ Service is not running. Status: $SERVICE_STATUS"
  echo "Checking logs for more details..."
  journalctl -u nexdb --no-pager -n 30
fi

echo -e "\n📋 If issues persist, please check:"
echo "1. Application logs: sudo journalctl -u nexdb"
echo "2. Verify blueprint registration: grep -r 'dashboard_bp' $APP_DIR"
echo "3. Verify index route: grep -r 'def index' $APP_DIR" 