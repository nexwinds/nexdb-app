#!/bin/bash
# nexdb-uninstall.sh - Uninstallation script for NEXDB
# Supports both interactive and force modes

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "\n❌ This script must be run as root. Please use sudo."
  exit 1
fi

# Check for --force flag
FORCE_MODE=false
if [[ "$1" == "--force" ]]; then
  FORCE_MODE=true
  echo -e "\n🔄 NEXDB Force Uninstaller"
  echo -e "=========================="
  echo -e "⚠️ Force mode enabled. NO confirmation will be requested."
else
  echo -e "\n🔄 NEXDB Uninstaller"
  echo -e "===================="
fi

# Stop and disable the service
echo -e "\n🛑 Stopping NEXDB service..."
systemctl stop nexdb 2>/dev/null || true
systemctl disable nexdb 2>/dev/null || true

# Remove systemd service
echo -e "\n🗑️ Removing systemd service..."
rm -f /etc/systemd/system/nexdb.service
systemctl daemon-reload

# Remove firewall rules
echo -e "\n🧱 Removing firewall rules..."
if command -v ufw &> /dev/null; then
  ufw delete allow 8080/tcp &> /dev/null || true
  echo "UFW rules removed"
fi

if command -v ip6tables &> /dev/null; then
  ip6tables -D INPUT -p tcp --dport 8080 -j ACCEPT &> /dev/null || true
  echo "IP6Tables rules removed"
fi

# Ask for confirmation before deleting files (unless in force mode)
if [ "$FORCE_MODE" = false ]; then
  # Check if script is running in a pipe (e.g., curl | bash)
  if [ -t 0 ]; then
    # Running in interactive terminal
    echo -e "\n⚠️ Warning: This will delete all NEXDB files and data, including backups."
    echo -e "MySQL and PostgreSQL databases will NOT be removed."
    echo -e "Are you sure you want to continue? (y/n)"
    read -n 1 -r REPLY
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo -e "\n❌ Uninstallation cancelled. Service is still disabled but files remain."
      exit 1
    fi
  else
    # Running in a pipe (e.g., curl | bash)
    echo -e "\n⚠️ Warning: This script appears to be running from a pipe (curl | bash)."
    echo -e "Interactive confirmation is not possible in this mode."
    echo -e "Please run this script directly with one of the following methods:"
    echo -e "  1. Download and run: wget https://raw.githubusercontent.com/nexwinds/nexdb-app/main/nexdb-uninstall.sh && sudo bash nexdb-uninstall.sh"
    echo -e "  2. Use force mode: curl -sSL https://raw.githubusercontent.com/nexwinds/nexdb-app/main/nexdb-uninstall.sh | sudo bash -s -- --force"
    echo -e "\n❌ Uninstallation cancelled. Service is disabled but files remain."
    exit 1
  fi
fi

# Remove application directory
echo -e "\n🗑️ Removing NEXDB files..."
rm -rf /opt/nexdb

echo -e "\n✅ NEXDB has been uninstalled successfully!"
echo -e "Note: MySQL and PostgreSQL databases have not been removed."
echo -e "If you want to remove them as well, run:"
echo -e "  - For MySQL: sudo apt purge mysql-server"
echo -e "  - For PostgreSQL: sudo apt purge postgresql postgresql-contrib" 