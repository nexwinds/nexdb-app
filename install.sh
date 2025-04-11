#!/bin/bash

# NEXDB - Installation script for Ubuntu 24.04
# Run as: sudo ./install.sh

# Exit on error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (with sudo)"
  exit 1
fi

# Check Ubuntu version
VERSION=$(lsb_release -rs)
if [ "$VERSION" != "24.04" ]; then
  echo "This script is designed for Ubuntu 24.04."
  echo "Your version: $VERSION"
  read -p "Continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

echo "=== NEXDB Installation ==="
echo "Installing on Ubuntu $VERSION"

# Update package lists
echo "Updating package lists..."
apt-get update

# Install system dependencies
echo "Installing system dependencies..."
apt-get install -y python3 python3-pip python3-venv python3-dev build-essential libssl-dev \
  mysql-client postgresql-client ufw nano

# Create nexdb user if it doesn't exist
if ! id "nexdb" &>/dev/null; then
  echo "Creating nexdb user..."
  useradd -m -s /bin/bash nexdb
  echo "nexdb ALL=(ALL) NOPASSWD: /usr/sbin/ufw" >> /etc/sudoers.d/nexdb
fi

# Set installation directory
INSTALL_DIR="/opt/nexdb"

# Create install directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
  echo "Creating installation directory..."
  mkdir -p $INSTALL_DIR
fi

# Copy application files
echo "Installing NEXDB application..."
cp -R . $INSTALL_DIR

# Set ownership
chown -R nexdb:nexdb $INSTALL_DIR

# Set up Python virtual environment
echo "Setting up Python virtual environment..."
cd $INSTALL_DIR
sudo -u nexdb python3 -m venv venv
sudo -u nexdb venv/bin/pip install --upgrade pip
sudo -u nexdb venv/bin/pip install -r requirements.txt
sudo -u nexdb venv/bin/pip install gunicorn

# Create backup directory
mkdir -p /var/backups/nexdb
chown -R nexdb:nexdb /var/backups/nexdb

# Generate random secret key
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 16)

# Create .env file
echo "Creating environment configuration..."
cat > $INSTALL_DIR/.env << EOF
# Flask settings
FLASK_APP=app.py
FLASK_ENV=production
FLASK_CONFIG=production
SECRET_KEY=$SECRET_KEY
DEBUG=False

# Database URL for the application itself
DATABASE_URL=sqlite:///app.sqlite

# JWT settings
JWT_SECRET_KEY=$JWT_SECRET_KEY

# S3 Backup settings
S3_BUCKET=
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_REGION=us-east-1

# Database server default credentials
MYSQL_DEFAULT_HOST=localhost
MYSQL_DEFAULT_PORT=3306
POSTGRES_DEFAULT_HOST=localhost
POSTGRES_DEFAULT_PORT=5432

# Encryption key for database credentials
ENCRYPTION_KEY=$ENCRYPTION_KEY

# Backup directory
BACKUP_DIR=/var/backups/nexdb
EOF

chown nexdb:nexdb $INSTALL_DIR/.env
chmod 600 $INSTALL_DIR/.env

# Set up systemd service
echo "Setting up systemd service..."
cat > /etc/systemd/system/nexdb.service << EOF
[Unit]
Description=NEXDB - Modern Web-Based Database Control Panel
After=network.target

[Service]
User=nexdb
Group=nexdb
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable nexdb.service

# Configure UFW
echo "Configuring firewall..."
ufw allow 5000/tcp
ufw allow ssh

if ! ufw status | grep -q "Status: active"; then
  echo "Enabling UFW..."
  ufw --force enable
fi

# Initialize database and create admin user
echo "Initializing database..."
cd $INSTALL_DIR
sudo -u nexdb venv/bin/flask init-db

# Prompt for admin user creation
echo "Creating admin user..."
read -p "Admin username: " ADMIN_USER
read -p "Admin email: " ADMIN_EMAIL
read -s -p "Admin password: " ADMIN_PASS
echo ""

sudo -u nexdb venv/bin/flask create-admin "$ADMIN_USER" "$ADMIN_EMAIL" "$ADMIN_PASS"

# Start the service
echo "Starting NEXDB service..."
systemctl start nexdb.service

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo "=== Installation complete! ==="
echo "NEXDB is now running."
echo "Access the web interface at: http://$SERVER_IP:5000"
echo ""
echo "Login with:"
echo "Username: $ADMIN_USER"
echo "Email: $ADMIN_EMAIL"
echo ""
echo "Remember to configure HTTPS for production use!" 