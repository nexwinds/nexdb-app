#!/bin/bash
# verify-installation.sh - Verify NEXDB installation

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "\n❌ This script must be run as root. Please use sudo."
  exit 1
fi

INSTALL_DIR="/opt/nexdb"
echo -e "\n🔍 NEXDB Installation Verification"
echo -e "================================="

# Check if directory exists
echo -e "\n📂 Checking installation directory..."
if [ -d "$INSTALL_DIR" ]; then
  echo -e "✅ Installation directory exists at $INSTALL_DIR"
  
  # Count files
  FILE_COUNT=$(find $INSTALL_DIR -type f | wc -l)
  echo -e "   Found $FILE_COUNT files in the installation directory"
else
  echo -e "❌ Installation directory not found at $INSTALL_DIR"
  echo -e "   NEXDB may not be installed correctly"
  exit 1
fi

# Check systemd service
echo -e "\n⚙️ Checking systemd service..."
if systemctl list-unit-files | grep -q nexdb.service; then
  echo -e "✅ Systemd service is installed"
  
  # Check service status
  SERVICE_STATUS=$(systemctl is-active nexdb)
  if [ "$SERVICE_STATUS" = "active" ]; then
    echo -e "✅ Service is active and running"
  else
    echo -e "❌ Service is installed but not running (status: $SERVICE_STATUS)"
    echo -e "   Run 'sudo systemctl start nexdb' to start the service"
  fi
else
  echo -e "❌ Systemd service not found"
  echo -e "   You may need to reinstall NEXDB"
fi

# Check network
echo -e "\n🌐 Checking network connectivity..."
IP=$(hostname -I | awk '{print $1}')
echo -e "   Server IP: $IP"

# Check port binding
echo -e "\n🔌 Checking port binding..."
if lsof -i :8080 | grep -q python; then
  echo -e "✅ Port 8080 is in use by Python (NEXDB running)"
elif lsof -i :8080 | grep -q -i "LISTEN"; then
  echo -e "⚠️ Port 8080 is in use, but not by NEXDB"
  echo -e "   This may indicate a port conflict"
  lsof -i :8080
else
  echo -e "❌ Nothing is listening on port 8080"
  echo -e "   NEXDB may not be running correctly"
fi

# Check firewall
echo -e "\n🧱 Checking firewall rules..."
if command -v ufw &> /dev/null; then
  if ufw status | grep -q "8080/tcp"; then
    echo -e "✅ Port 8080 is allowed in UFW"
  else
    echo -e "⚠️ Port 8080 may not be allowed in the firewall"
    echo -e "   Run 'sudo ufw allow 8080/tcp' to open it"
  fi
else
  echo -e "ℹ️ UFW is not installed"
fi

# Test web service
echo -e "\n🌐 Testing web service..."
CURL_OUTPUT=$(curl -s -m 5 http://localhost:8080/health 2>&1)
if [ $? -eq 0 ]; then
  echo -e "✅ Web service is responding on localhost"
  echo -e "   Response: $CURL_OUTPUT"
else
  echo -e "❌ Web service is not responding on localhost"
  echo -e "   This indicates that NEXDB is not running correctly"
fi

echo -e "\n📋 Verification complete!"
echo -e "   If any issues were found, refer to the troubleshooting guide:"
echo -e "   TROUBLESHOOTING.md"
echo -e "\n   Or use the fix script to attempt automatic repairs:"
echo -e "   sudo bash nexdb-fix.sh" 