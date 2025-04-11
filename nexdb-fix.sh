#!/bin/bash
# nexdb-fix.sh - Fix script for NEXDB import error

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "\n❌ This script must be run as root. Please use sudo."
  exit 1
fi

INSTALL_DIR="/opt/nexdb"

echo -e "\n🛠️ NEXDB Fix Script"
echo -e "=================="

# Stop the service
echo -e "\n🛑 Stopping NEXDB service..."
systemctl stop nexdb

# Fix the main entry point to correctly import the run_app function
echo -e "\n🔧 Creating the correct Python entry point..."
mkdir -p "$INSTALL_DIR/app"

# Create the correct __main__.py file
cat << EOF > $INSTALL_DIR/app/__main__.py
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

echo -e "\n✅ Entry point has been fixed."

# Reload and restart the service
echo -e "\n🔄 Restarting NEXDB service..."
systemctl daemon-reload
systemctl restart nexdb

# Check service status
sleep 2
SERVICE_STATUS=$(systemctl is-active nexdb)
if [ "$SERVICE_STATUS" != "active" ]; then
  echo -e "\n⚠️ Service is still not running properly. Status: $SERVICE_STATUS"
  echo -e "Checking logs for more details:"
  journalctl -u nexdb --no-pager -n 20
  
  echo -e "\n🔍 Additional debugging:"
  echo -e "1. Testing Python module import:"
  pushd $INSTALL_DIR > /dev/null
  $INSTALL_DIR/venv/bin/python3 -c "import sys; print(sys.path); import app; print('App module found')"
  popd > /dev/null
  
  echo -e "\n2. Checking file structure:"
  ls -la $INSTALL_DIR
  echo -e "\nApp directory content:"
  ls -la $INSTALL_DIR/app
  
  echo -e "\n💡 If the fix didn't work, you may need to uninstall and reinstall NEXDB:"
  echo -e "   sudo ./nexdb-uninstall.sh"
  echo -e "   sudo ./nexdb-install.sh"
else
  echo -e "\n✅ Service is running successfully!"
  IP=$(hostname -I | awk '{print $1}')
  echo -e "\n🎉 NEXDB is now running at: http://$IP:8080"
  echo -e "🔐 Admin Login:"
  echo -e "   Username: admin"
  echo -e "   Password: admin123 (or check config/__init__.py)"
fi 