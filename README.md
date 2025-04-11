# NEXDB - Modern Web-Based Database Control Panel

NEXDB is a sleek and secure web-based control panel for managing MySQL and PostgreSQL databases on Ubuntu 24.04. It serves as a more secure, maintainable, and user-friendly alternative to tools like EasyPanel or CloudPanel.

## Core Features

### Database Management
- Create and manage MySQL/PostgreSQL databases and users
- Securely handle credentials
- Configure UFW for controlled remote access

### Backup System
- Support for on-demand and scheduled backups
- Seamless integration with Amazon S3 for remote storage

### Project Organization
- Group related databases under "projects" for cleaner management

### User Management
- Role-based access control
- Secure session handling for web users

### Frontend
- Built with Tailwind CSS and semantic HTML
- Fully responsive and accessibility-friendly UI

## Technical Stack
- Backend: Python 3.10+, Flask 2.3+
- Databases Supported: MySQL & PostgreSQL
- Authentication: JWT (for API), Session-based (for web)

## Security Features
- Secure password hashing
- Input sanitization
- CSRF protection
- Rate limiting
- Proper security headers

## Installation

### Prerequisites
- Ubuntu 24.04
- Python 3.10+
- MySQL and/or PostgreSQL

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/nexdb.git
cd nexdb
```

2. Run the installation script:
```bash
sudo ./install.sh
```

3. Access the web interface at:
```
http://your-server-ip:5000
```

## Development

### Setup Development Environment
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run development server
flask run
```

## License
[MIT License](LICENSE) 