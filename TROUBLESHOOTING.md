# NEXDB Troubleshooting Guide

## Connection Issues (ERR_CONNECTION_REFUSED)

If you're encountering an `ERR_CONNECTION_REFUSED` error when trying to access NEXDB, follow these troubleshooting steps:

### 1. Verify NEXDB Service Status

SSH into your server and check if the NEXDB service is running:

```bash
sudo systemctl status nexdb
```

If the service is not running or showing errors, try restarting it:

```bash
sudo systemctl restart nexdb
```

To view detailed logs:

```bash
sudo journalctl -u nexdb --no-pager
```

### 2. Check Firewall Settings

Make sure port 8080 is open in your firewall:

```bash
sudo ufw status
```

If port 8080 is not listed as allowed, open it:

```bash
sudo ufw allow 8080/tcp
sudo ufw reload
```

### 3. Verify Network Connectivity

Use the included test script to check connectivity from your local machine:

```bash
python test_connection.py <server_ip> 8080
```

You can also use telnet to test basic connectivity:

```bash
telnet <server_ip> 8080
```

### 4. Check the Application Configuration

Ensure the application is configured to listen on all interfaces:

1. Check `config/__init__.py`:
   ```python
   HOST = "0.0.0.0"  # Must be 0.0.0.0 to accept connections from any IP
   PORT = 8080
   ```

2. If you change this setting, restart the service:
   ```bash
   sudo systemctl restart nexdb
   ```

### 5. Test the Health Check Endpoint

Try accessing the health check endpoint which is designed to be minimal and reliable:

```
http://<server_ip>:8080/health
```

### 6. Check for Port Conflicts

Make sure no other service is using port 8080:

```bash
sudo lsof -i :8080
```

### 7. Server Firewall/Security Group Settings

If you're using a cloud provider (AWS, DigitalOcean, etc.), check that port 8080 is allowed in your security group/firewall settings in the cloud console.

### 8. Proxy Configuration

If you're using a reverse proxy (like Nginx), verify the proxy configuration:

```bash
sudo nano /etc/nginx/sites-available/nexdb
```

Make sure it's correctly forwarding requests to `localhost:8080`.

### 9. DNS Issues

If you're accessing the server via a domain name, verify DNS resolution:

```bash
nslookup yourdomain.com
```

### 10. Try Accessing via IP Address

If you've been using a domain name, try accessing directly via IP address:

```
http://<server_ip>:8080
```

### 11. Advanced: Check System Resources

Verify the server has enough resources to run the application:

```bash
free -m       # Check memory
df -h         # Check disk space
top           # Check CPU usage
```

## Python Import Error

If you see an error like `ImportError: cannot import name 'run_app' from 'app'` in the logs, this is a Python module import issue. This can happen when the Python module structure is not properly set up.

### Fix for Import Error

1. You can use the provided fix script:
   ```bash
   sudo bash nexdb-fix.sh
   ```

2. Or manually fix the issue:
   ```bash
   sudo systemctl stop nexdb
   
   # Create or edit the main entry point
   sudo nano /opt/nexdb/app/__main__.py
   ```
   
   Replace the content with:
   ```python
   # Fix for correctly importing the run_app function
   import os
   import sys
   
   # Add the parent directory to the path so we can import app
   sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   
   # Now we can import run_app from app
   from app import run_app
   
   if __name__ == '__main__':
       run_app()
   ```
   
3. Restart the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart nexdb
   ```

## Using the Test Connection Script

We've provided a `test_connection.py` script to help diagnose connection issues. Run it with:

```bash
# Install required packages if needed
pip install requests

# Run the test
python test_connection.py <server_ip> 8080
```

This script will check if:
1. The port is open on the server
2. The HTTP server is responding
3. Any connection issues are occurring

## Need More Help?

If you're still experiencing issues after following these steps, please:

1. Gather all relevant logs:
   ```bash
   sudo journalctl -u nexdb --no-pager > nexdb_logs.txt
   ```

2. Note your server environment:
   ```bash
   lsb_release -a > server_info.txt
   ufw status >> server_info.txt
   ```

3. Open an issue on our GitHub repository or contact support with these files attached. 