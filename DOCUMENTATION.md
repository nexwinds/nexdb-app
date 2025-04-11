# NEXDB Documentation

## Overview

NEXDB is a lightweight, intuitive web-based control panel for managing MySQL and PostgreSQL databases on Ubuntu 24.04 LTS. Built with Python (Flask) and styled with Tailwind CSS, NEXDB provides essential database management tools through a simple, secure web interface.

## System Architecture

### Technology Stack

- **Backend**: Python 3.10+ / Flask
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Databases**: SQLite (for application data), MySQL, PostgreSQL (managed services)
- **Authentication**: Session-based with token support for API
- **Deployment**: systemd service (port 8080)

### Application Structure

The application follows a modular architecture for better maintainability:

```
/opt/nexdb/
├── app/                    # Flask application
│   ├── models/             # Database models
│   │   ├── __init__.py     # Database initialization
│   │   ├── user.py         # User model
│   │   ├── backup.py       # Backup model
│   │   └── db_credential.py # Database credentials model
│   ├── routes/             # API and web routes
│   │   ├── __init__.py     # Route registration
│   │   ├── api.py          # API endpoints
│   │   ├── auth.py         # Authentication routes
│   │   ├── backup.py       # Backup management routes
│   │   ├── dashboard.py    # Dashboard routes
│   │   ├── database.py     # Database management routes
│   │   ├── projects.py     # Project management routes
│   │   ├── settings.py     # Settings routes
│   │   └── user.py         # User management routes
│   ├── services/           # Business logic
│   │   ├── backup_service.py   # Backup operations
│   │   ├── db_service.py       # Database operations
│   │   ├── scheduler_service.py # Scheduling operations
│   │   └── user_service.py     # User management operations
│   ├── static/             # Static assets (CSS, JS, images)
│   ├── templates/          # Tailwind HTML templates
│   │   ├── auth/           # Authentication templates
│   │   ├── backup/         # Backup management templates
│   │   ├── dashboard/      # Dashboard templates
│   │   ├── database/       # Database management templates
│   │   ├── projects/       # Project templates
│   │   └── base.html       # Base template with layout
│   └── __init__.py         # Application initialization
├── config/                 # Configuration files
│   └── __init__.py         # Configuration parameters
├── backups/                # Backup storage location
├── nexdb-install.sh        # Installation script
└── requirements.txt        # Python dependencies
```

## Features

### Database Management

- **MySQL and PostgreSQL Support**: Create and manage databases in both systems
- **User Management**: Create database users with appropriate permissions
- **Credential Storage**: Securely store and display database credentials
- **Port Management**: Open external database ports via UFW for remote access

### Backup Solutions

- **On-Demand Backups**: Create backups of databases as needed
- **Scheduled Backups**: Configure recurring backups (daily, weekly, monthly)
- **Remote Storage**: Optional Amazon S3 integration for backup storage
- **Backup Management**: Download, view, and delete backups

### User Management

- **Role-Based Access**: Administrator and regular user roles
- **User Preferences**: Individual settings and theme preferences
- **Session Management**: Configurable session timeouts and security features

### API Interface

- **RESTful Design**: Consistent API design following REST principles
- **Token Authentication**: Secure API access using token-based authentication
- **Comprehensive Endpoints**: Complete coverage of all web interface functions

## Installation Guide

### Requirements

- Ubuntu 24.04 LTS
- sudo privileges
- Internet connection

### Automatic Installation

```bash
curl -sSL https://raw.githubusercontent.com/nexwinds/nexdb-app/main/nexdb-install.sh | sudo bash
```

### Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/nexwinds/nexdb-app.git
```

2. Run the installation script:
```bash
cd nexdb-app
chmod +x nexdb-install.sh
sudo ./nexdb-install.sh
```

### Post-Installation

After installation:
1. Access NEXDB at `http://<your-server-ip>:8080`
2. Log in with the admin credentials displayed during installation
3. Change the default admin password immediately
4. Configure your first database

## Security Considerations

### Best Practices

1. **Change Default Credentials**: Always change the default admin password after installation
2. **Use HTTPS**: Place NEXDB behind a reverse proxy (like Nginx) with SSL/TLS
3. **Firewall Rules**: Restrict access to the web interface using IP-based rules
4. **Regular Updates**: Keep the application and its dependencies updated
5. **Backup Your Backups**: Ensure backups are stored in multiple locations

### Known Limitations

- Default installation uses HTTP, not HTTPS
- API tokens are regenerated on application restart
- No built-in brute force protection for login attempts

## API Reference

### Authentication

All API requests (except `/api/status`) require an `X-API-Token` header.

```bash
curl -H "X-API-Token: your_api_token" http://<your-ip>:8080/api/databases
```

### Endpoints

#### Database Management

- `GET /api/databases` - List all databases
- `POST /api/databases/create` - Create a new database
- `POST /api/users/create` - Create a new database user
- `POST /api/ports/open/<db_type>` - Open database port

#### Backup Management

- `GET /api/backups` - List all backups
- `POST /api/backups/create` - Create a new backup
- `POST /api/backups/schedule` - Schedule recurring backups

#### System Information

- `GET /api/status` - Get API status (no authentication required)
- `GET /api/token` - Get API token (for initial setup only)

## Troubleshooting

### Common Issues

1. **Installation Fails**: Ensure you're using Ubuntu 24.04 LTS and have internet access
2. **Login Issues**: Check that the correct credentials are being used
3. **Database Creation Fails**: Verify MySQL/PostgreSQL are properly installed
4. **Backup Failures**: Check disk space and permissions

### Logs

Application logs can be viewed using:

```bash
sudo journalctl -u nexdb.service
```

## Development Guide

### Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/nexwinds/nexdb-app.git
```

2. Install dependencies: 
```bash
pip install -r requirements.txt
```

3. Run in development mode: 
```bash
python -m app
```

### Coding Standards

- Follow PEP 8 for Python code style
- Use semantic HTML for templates
- Follow DRY (Don't Repeat Yourself) and KISS (Keep It Simple, Stupid) principles
- Implement modular components for maintainability
- Place components and APIs in feature or page directories

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License. 