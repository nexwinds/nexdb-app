#!/bin/bash

# Fix script for NEXDB installation
INSTALL_DIR="/opt/nexdb"
MAIN_FILE="$INSTALL_DIR/app/__main__.py"

echo "🔧 Fixing NEXDB installation..."

# Create the correct __main__.py file
echo "📝 Creating the correct Python entry point..."
mkdir -p "$INSTALL_DIR/app"

cat << EOF > $MAIN_FILE
# Fix for correctly importing the run_app function
import os
import sys

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import run_app from app
from app import run_app

if __name__ == '__main__':
    run_app()
EOF

# Set proper permissions
echo "🔒 Setting correct permissions..."
chmod 644 $MAIN_FILE

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
    echo "✅ Web service is responding on localhost!"
    IP=$(hostname -I | awk '{print $1}')
    echo -e "\n🎉 NEXDB should now be accessible at: http://$IP:8080"
  else
    echo "⚠️ Web service is not responding on localhost:8080."
    echo "This may indicate another issue. Please check the logs:"
    echo "sudo journalctl -u nexdb --no-pager -n 20"
  fi
else
  echo "⚠️ Service is still not running. Status: $SERVICE_STATUS"
  echo "Checking logs for more details..."
  journalctl -u nexdb --no-pager -n 20
fi

echo -e "\n📋 If issues persist, please check:"
echo "1. Python path: $(which python3)"
echo "2. App directory structure: ls -la $INSTALL_DIR/app/"
echo "3. Virtual environment: $INSTALL_DIR/venv/bin/python3 -m pip list" 