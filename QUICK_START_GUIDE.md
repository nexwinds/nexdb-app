# NEXDB Quick Start Guide

## What is NEXDB?

NEXDB is a lightweight web-based control panel for managing MySQL and PostgreSQL databases on Ubuntu 24.04 LTS. It provides an easy-to-use interface for common database management tasks.

## Installation

### Prerequisites

- Ubuntu 24.04 LTS server
- sudo privileges
- Internet connection

### One-Line Installation

```bash
curl -sSL https://raw.githubusercontent.com/yourusername/nexdb/main/nexdb-install.sh | sudo bash
```

## Getting Started

### First Login

1. Access NEXDB at `http://<your-server-ip>:8080`
2. Log in with the admin credentials displayed during installation
3. **Important**: Change your admin password immediately by going to Settings

### Creating Your First Database

1. Navigate to the "Databases" section in the sidebar
2. Click "Create New Database" 
3. Select the database type (MySQL or PostgreSQL)
4. Enter a name for your database
5. Click "Create"

### Creating a Database User

1. In the Databases section, find your database
2. Click "Create User"
3. Enter a username
4. Set permissions as needed
5. Save the displayed password securely!

### Creating a Backup

1. Navigate to the "Backups" section
2. Click "Create New Backup"
3. Select the database to back up
4. Click "Create Backup"

### Setting Up Scheduled Backups

1. In the Backups section, click "Schedule Backup"
2. Select your database
3. Choose a backup frequency (daily, weekly, monthly)
4. Configure optional S3 storage settings
5. Click "Save Schedule"

## Common Tasks

### Opening a Database Port for Remote Access

1. In the Databases section, find your database
2. Click "Settings"
3. Click "Open External Port" 
4. Confirm the security warning

### Managing User Access

1. Navigate to the "Users" section in the sidebar
2. Create, edit, or remove users as needed
3. Set appropriate access levels

### Accessing from API

1. Go to "Settings" → "API Access"
2. Copy your API token
3. Use the token in HTTP headers: `X-API-Token: your_token_here`

## Getting Help

For more information, refer to the full documentation:
- [Complete Documentation](DOCUMENTATION.md)
- [API Reference](DOCUMENTATION.md#api-reference)

## Security Best Practices

1. Always change the default admin password
2. Consider placing NEXDB behind a reverse proxy with SSL
3. Use strong passwords for both NEXDB and database users
4. Regularly backup your databases
5. Keep NEXDB updated 