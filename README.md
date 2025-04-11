# 🚀 NEXDB – Next Generation Server Control Panel to Manage Databases

**NEXDB** is a lightweight, intuitive, and script-deployable control panel to manage **MySQL** and **PostgreSQL** databases on Ubuntu 24.04 LTS. Built with **Python (Flask)** and styled using **Tailwind CSS**, NEXDB empowers developers and sysadmins with essential database tools from a simple, secure web interface.

![NEXDB Banner](https://via.placeholder.com/800x400?text=NEXDB+Dashboard)

## 🔧 Features

- ✅ **Database Management**
  - Install & manage MySQL and PostgreSQL databases
  - Create database users with granular permissions
  - View and manage database credentials
  - Open external database ports (UFW) with a single click

- 💾 **Backup Solutions**
  - Create on-demand database backups
  - Schedule automated backups (daily, weekly, monthly)
  - Integration with Amazon S3 for remote backup storage
  - Download or delete backups from the web interface

- 👥 **Multi-User Support**
  - Role-based access control
  - Admin and regular user accounts
  - Individual user settings and preferences

- 🔄 **Theme Support**
  - Toggle between light and dark themes
  - Personalized theme preferences per user

- 🧰 **API Interface**
  - RESTful API for automation and scripting
  - Token-based authentication for secure API access
  - Complete API documentation included

- 🛡️ **Security Features**
  - Session timeout configuration
  - Secure password management
  - System runs as a systemd service on port `8080`

## 📦 Installation

> ⚠️ Supported on: **Ubuntu 24.04 LTS**

### One-Line Installation

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

The script will:
- Install all dependencies (Python, MySQL, PostgreSQL)
- Set up the Flask application with database support
- Configure systemd service for automatic startup
- Create an admin user and secure password
- Start NEXDB on http://<your-ip>:8080

### Verifying Your Installation

After installation, you can verify that everything is working correctly:

```bash
sudo bash verify-installation.sh
```

This script will check:
- Installation directory and files
- Systemd service status
- Network connectivity and port bindings
- Firewall rules
- Web service response

## 🔐 Accessing the Panel

After installation, open your browser:

```
http://<your-server-ip>:8080
```

Log in using the admin credentials displayed at the end of the installation.

## 🛠️ Troubleshooting

If you encounter issues during installation or when accessing the panel, we provide several scripts to help:

### Common Issues

1. **ERR_CONNECTION_REFUSED**: If you can't connect to the panel, check that the service is running:
   ```bash
   sudo systemctl status nexdb
   ```

2. **Python Import Error**: If logs show `ImportError: cannot import name 'run_app' from 'app'`, use our fix script:
   ```bash
   sudo bash nexdb-fix.sh
   ```

### Provided Scripts

- **nexdb-fix.sh**: Resolves common Python module import issues without requiring a full reinstallation
- **nexdb-uninstall.sh**: Completely removes NEXDB from your system (keeps database data intact)
- **verify-installation.sh**: Checks if your installation is working correctly
- **test_connection.py**: Tests connectivity to the NEXDB server from your local machine

For comprehensive troubleshooting steps, refer to our [Troubleshooting Guide](TROUBLESHOOTING.md).

## 🖥️ Dashboard Preview

![NEXDB Dashboard](https://via.placeholder.com/800x400?text=NEXDB+Dashboard+Preview)

## 📁 Project Structure

```
/opt/nexdb/
├── app/                    # Flask application
│   ├── models/             # Database models (user, backup, db_credential)
│   ├── routes/             # API and web routes (api, auth, backup, database, etc.)
│   ├── services/           # Business logic
│   ├── static/             # CSS, JS, images
│   └── templates/          # Tailwind HTML templates
├── config/                 # Configuration files
├── backups/                # Backup destination
├── nexdb-install.sh        # Installation script
├── nexdb-fix.sh            # Troubleshooting script for common issues
├── nexdb-uninstall.sh      # Uninstallation script
├── verify-installation.sh  # Installation verification script
└── requirements.txt        # Python dependencies
```

## 🚀 Example API Usage

### Get a list of databases:

```bash
curl -H "X-API-Token: your_api_token" http://<your-ip>:8080/api/databases
```

### Create a new database:

```bash
curl -X POST -H "X-API-Token: your_api_token" \
  -H "Content-Type: application/json" \
  -d '{"db_type": "mysql", "db_name": "my_new_db"}' \
  http://<your-ip>:8080/api/databases/create
```

### Create a database backup:

```bash
curl -X POST -H "X-API-Token: your_api_token" \
  -H "Content-Type: application/json" \
  -d '{"db_type": "postgres", "db_name": "my_database"}' \
  http://<your-ip>:8080/api/backups/create
```

## 🔐 Security Recommendations

- Change the admin password immediately after installation
- Consider placing NEXDB behind a reverse proxy with SSL (like Nginx)
- Restrict access to the web interface using IP-based firewall rules
- Regularly update the application and its dependencies

## 🔄 Upgrading and Maintenance

To upgrade NEXDB to a newer version:

1. First, back up any custom configurations
2. Uninstall the current version:
   ```bash
   sudo bash nexdb-uninstall.sh
   ```
3. Install the new version using the installation script

For minor fixes, you can use the fix script without a full reinstallation:
```bash
sudo bash nexdb-fix.sh
```

## 🤝 Contributing

Pull requests are welcome! Please feel free to submit issues for bugs or feature requests.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Crafted with ❤️ by [Diogo Cardoso](https://github.com/nexwinds)

*NEXDB - Simple tools for powerful people.* 