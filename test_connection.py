import sys
import socket
import requests
import time

def check_port(host, port, timeout=5):
    """Check if a port is open on a host."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def test_http_connection(url, max_retries=3):
    """Test HTTP connection to a URL with retries."""
    print(f"Testing connection to {url}")
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}/{max_retries}...")
            response = requests.get(url, timeout=10)
            print(f"Connection successful! Status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            return True
        except requests.exceptions.ConnectionError:
            print(f"Connection error on attempt {attempt}")
        except requests.exceptions.Timeout:
            print(f"Connection timed out on attempt {attempt}")
        except Exception as e:
            print(f"Error: {str(e)}")
        
        if attempt < max_retries:
            print("Retrying in 2 seconds...")
            time.sleep(2)
    
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_connection.py <server_ip> [port]")
        sys.exit(1)
    
    server_ip = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    
    # Check if port is open
    print(f"Checking if port {port} is open on {server_ip}...")
    if check_port(server_ip, port):
        print(f"Port {port} is OPEN on {server_ip}")
    else:
        print(f"Port {port} is CLOSED on {server_ip}")
    
    # Test HTTP connection
    url = f"http://{server_ip}:{port}"
    if not test_http_connection(url):
        print("\nConnection test failed. Possible issues:")
        print("1. Server is not running")
        print("2. Firewall is blocking the connection")
        print("3. Network issues between your machine and the server")
        print("\nTroubleshooting steps:")
        print("1. Check if NEXDB service is running on the server")
        print("   - SSH to the server and run: sudo systemctl status nexdb")
        print("2. Verify firewall settings")
        print("   - SSH to the server and run: sudo ufw status")
        print("   - Ensure port 8080 is allowed: sudo ufw allow 8080/tcp")
        print("3. Check if the application is correctly binding to 0.0.0.0")
        print("   - Modify config/__init__.py to set HOST = \"0.0.0.0\"")
        print("   - Restart the service: sudo systemctl restart nexdb") 