#!/bin/bash

# NEXDB Direct Uninstall Script
echo "🧹 NEXDB Uninstallation"
echo "====================="

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
  echo "❌ This script must be run as root"
  exit 1
fi

# Installation directory and service file
INSTALL_DIR="/opt/nexdb"
SERVICE_FILE="/etc/systemd/system/nexdb.service"

echo "🛑 Stopping and disabling NEXDB service..."
systemctl stop nexdb
systemctl disable nexdb

echo "🗑️ Removing systemd service..."
rm -f "$SERVICE_FILE"
systemctl daemon-reload

echo "🔥 Removing firewall rule..."
ufw delete allow 8080/tcp

echo "📂 Removing NEXDB installation directory..."
rm -rf "$INSTALL_DIR"

echo "✅ NEXDB has been completely uninstalled from your system."
echo "If you want to reinstall it in the future, simply run the installation script again." 