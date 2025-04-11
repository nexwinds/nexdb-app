#!/bin/bash
# nexdb-uninstall-force.sh - Force uninstallation script for NEXDB (no confirmation required)

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "\n❌ This script must be run as root. Please use sudo."
  exit 1
fi

echo -e "\n🔄 NEXDB Force Uninstaller"
echo -e "=========================="
echo -e "⚠️  No confirmation will be requested. ALL NEXDB files will be removed."

# Stop and disable the service
echo -e "\n🛑 Stopping NEXDB service..."
systemctl stop nexdb 2>/dev/null || true
systemctl disable nexdb 2>/dev/null || true

# Remove systemd service
echo -e "\n🗑️  Removing systemd service..."
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

# Remove application directory without confirmation
echo -e "\n🗑️  Removing NEXDB files..."
rm -rf /opt/nexdb

echo -e "\n✅ NEXDB has been uninstalled successfully!"
echo -e "Note: MySQL and PostgreSQL databases have not been removed." 