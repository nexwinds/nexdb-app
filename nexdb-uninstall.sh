#!/bin/bash
# nexdb-uninstall.sh - Script to completely remove NEXDB from the system
# This will remove services, files, and clean up database entries

# Disable "exit on error" to better handle errors
set +e

echo -e "\n⚠️  NEXDB Uninstaller"
echo -e "===================="
echo -e "This script will completely remove NEXDB from your system including:"
echo -e "- The NEXDB service"
echo -e "- All NEXDB files in /opt/nexdb"
echo -e "- Firewall rules created for NEXDB"
echo -e "\nWARNING: This will NOT remove your databases or database servers (MySQL/PostgreSQL),"
echo -e "but will remove the NEXDB management interface."

# Confirm uninstallation
read -p "Are you sure you want to completely remove NEXDB? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo -e "\n❌ Uninstallation cancelled."
  exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "\n❌ This script must be run as root. Please use sudo."
  exit 1
fi

# Installation directory
INSTALL_DIR="/opt/nexdb"
SERVICE_FILE="/etc/systemd/system/nexdb.service"

echo -e "\n🛑 Stopping NEXDB service..."
systemctl stop nexdb
systemctl disable nexdb
echo "✅ Service stopped and disabled."

echo -e "\n🗑️ Removing systemd service file..."
if [ -f "$SERVICE_FILE" ]; then
  rm -f "$SERVICE_FILE"
  systemctl daemon-reload
  echo "✅ Service file removed."
else
  echo "❓ Service file not found. Skipping."
fi

echo -e "\n🧹 Removing NEXDB installation directory..."
if [ -d "$INSTALL_DIR" ]; then
  # Create backup of the data directory first if it exists
  if [ -d "$INSTALL_DIR/backups" ] && [ "$(ls -A "$INSTALL_DIR/backups")" ]; then
    BACKUP_DIR="/root/nexdb-backups-$(date +%Y%m%d-%H%M%S)"
    echo "📦 Creating backup of existing backups at $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    cp -r "$INSTALL_DIR/backups" "$BACKUP_DIR/"
    echo "✅ Backups saved to $BACKUP_DIR"
  fi
  
  # Remove NEXDB directory
  rm -rf "$INSTALL_DIR"
  echo "✅ Installation directory removed."
else
  echo "❓ Installation directory not found. Skipping."
fi

# Remove firewall rules
echo -e "\n🔥 Removing firewall rules..."
ufw delete allow 8080/tcp 2>/dev/null
echo "✅ Firewall rules removed."

# Check for and remove ip6tables rules if they exist
if [ -x "$(command -v ip6tables)" ]; then
  ip6tables -D INPUT -p tcp --dport 8080 -j ACCEPT 2>/dev/null
  echo "✅ IPv6 firewall rules removed."
fi

echo -e "\n🧹 Cleaning up..."
# Remove any log files
journalctl --vacuum-time=1s --unit=nexdb >/dev/null 2>&1
echo "✅ Logs cleaned."

echo -e "\n🎉 NEXDB has been successfully uninstalled!"
echo -e "\nNote: MySQL and PostgreSQL database servers are still installed."
echo -e "If you want to remove them as well, you can use the following commands:"
echo -e "- For MySQL: sudo apt remove --purge mysql-server mysql-client mysql-common -y && sudo rm -rf /var/lib/mysql /etc/mysql"
echo -e "- For PostgreSQL: sudo apt remove --purge postgresql postgresql-contrib -y && sudo rm -rf /var/lib/postgresql /etc/postgresql"
echo -e "\nThank you for using NEXDB!" 