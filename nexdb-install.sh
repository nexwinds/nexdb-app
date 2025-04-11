#!/bin/bash
# nexdb-install.sh - Installation script for NEXDB

# Disable "exit on error" to better handle errors
set +e

echo -e "\n🚀 Welcome to NEXDB Installer!"
echo -e "=============================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "\n❌ This script must be run as root. Please use sudo."
  exit 1
fi

# Check Ubuntu version
if [ ! -f /etc/lsb-release ] || ! grep -q "Ubuntu 24.04" /etc/lsb-release; then
  echo -e "\n⚠️  Warning: This script is optimized for Ubuntu 24.04 LTS. Your results may vary."
  read -p "Do you want to continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n❌ Installation cancelled."
    exit 1
  fi
fi

# Installation directory
INSTALL_DIR="/opt/nexdb"
mkdir -p $INSTALL_DIR

echo -e "\n📦 Updating system & installing dependencies..."
apt update && apt install -y \
  python3 python3-pip python3-venv \
  mysql-server postgresql postgresql-contrib \
  ufw curl git rsync

# Create Python virtual environment
echo -e "\n🐍 Setting up Python virtual environment..."
python3 -m venv $INSTALL_DIR/venv
source $INSTALL_DIR/venv/bin/activate

# Install Python dependencies
echo -e "\n📚 Installing Python dependencies..."
pip install -U flask flask-sqlalchemy werkzeug mysql-connector-python psycopg2-binary python-crontab boto3

# Get the absolute path of the script
SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")
SCRIPT_NAME=$(basename "$SCRIPT_PATH")

echo -e "\n📋 Copying application code to $INSTALL_DIR..."
echo -e "  Script path: $SCRIPT_PATH"
echo -e "  Script directory: $SCRIPT_DIR"

# Create backup directory
mkdir -p $INSTALL_DIR/backups

# First, explicitly copy this installation script to the destination
echo -e "\n📄 Copying installation script..."
cp "$SCRIPT_PATH" "$INSTALL_DIR/$SCRIPT_NAME"
if [ $? -eq 0 ]; then
  echo -e "  ✅ Installation script copied successfully to $INSTALL_DIR/$SCRIPT_NAME"
  chmod +x "$INSTALL_DIR/$SCRIPT_NAME"
else
  echo -e "  ❌ Failed to copy installation script. Continuing anyway..."
fi

# Use rsync to copy all other files, with explicit exclusions
echo -e "\n📁 Copying remaining files..."
rsync -av \
  --exclude=".git/" \
  --exclude=".ssh/" \
  --exclude="authorized_keys" \
  --exclude="id_rsa" \
  --exclude="id_rsa.pub" \
  --exclude="known_hosts" \
  --exclude="venv/" \
  --exclude="*.pyc" \
  --exclude="__pycache__/" \
  "$SCRIPT_DIR/" "$INSTALL_DIR/"

# Set permissions
echo -e "\n🔒 Setting permissions..."
chown -R root:root $INSTALL_DIR

# Create systemd service
echo -e "\n⚙️  Creating systemd service..."
cat << EOF > /etc/systemd/system/nexdb.service
[Unit]
Description=NEXDB Panel
After=network.target

[Service]
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python3 -m app
Restart=always
Environment="PATH=$INSTALL_DIR/venv/bin"
Environment="PYTHONPATH=$INSTALL_DIR"

[Install]
WantedBy=multi-user.target
EOF

# Create main entry point if it doesn't exist
if [ ! -f "$INSTALL_DIR/app/__main__.py" ]; then
  echo -e "\n📝 Creating main entry point..."
  mkdir -p "$INSTALL_DIR/app"
  cat << EOF > $INSTALL_DIR/app/__main__.py
from app import run_app

if __name__ == '__main__':
    run_app()
EOF
fi

# Allow web port in firewall
echo -e "\n🔥 Configuring firewall..."
ufw allow 8080/tcp

# Enable and start service
echo -e "\n🚀 Starting NEXDB service..."
systemctl daemon-reload
systemctl enable nexdb
systemctl start nexdb

# Get admin password from app config
if [ -f "$INSTALL_DIR/config/__init__.py" ]; then
  ADMIN_PASS=$(grep -oP "(?<=ADMIN_PASS = os.environ.get\('NEXDB_ADMIN_PASS', ')[^']*" $INSTALL_DIR/config/__init__.py)
  if [ -z "$ADMIN_PASS" ]; then
    ADMIN_PASS="admin123" # Fallback password if grep fails
    echo -e "⚠️  Warning: Could not extract admin password from config. Using default password"
  fi
else
  ADMIN_PASS="admin123" # Fallback password if config file not found
  echo -e "⚠️  Warning: Could not find config file. Using default admin password"
fi

# Display credentials & URL
IP=$(hostname -I | awk '{print $1}')
echo -e "\n🎉 NEXDB is now running at: http://$IP:8080"
echo -e "🔐 Admin Login:"
echo -e "   Username: admin"
echo -e "   Password: $ADMIN_PASS"
echo -e "📦 MySQL and PostgreSQL are ready to use."
echo -e "📁 Backups will be stored in $INSTALL_DIR/backups"
echo -e "\n💡 For security reasons, you should change the admin password after first login." 