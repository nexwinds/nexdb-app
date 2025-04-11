import subprocess
import re
import os
import mysql.connector
import psycopg2
from app.models import db
from app.models.db_credential import DBCredential

class Database:
    """Simple database model"""
    def __init__(self, name, db_type, size=0, tables=0, last_backup=None):
        self.name = name
        self.type = db_type  # 'mysql' or 'postgres'
        self.size = size
        self.tables = tables
        self.last_backup = last_backup

class Credential:
    """Database credential model"""
    def __init__(self, id, db_name, db_type, username, password, host='localhost'):
        self.id = id
        self.db_name = db_name
        self.db_type = db_type
        self.username = username
        self.password = password
        self.host = host

class DBService:
    """Service for database operations"""
    # In-memory credential storage (for development/fallback)
    _credentials = []
    
    @classmethod
    def get_mysql_databases(cls):
        """Get a list of MySQL databases"""
        try:
            # Try to execute the command to list MySQL databases
            result = subprocess.run(
                ['mysql', '-e', 'SHOW DATABASES'],
                capture_output=True, text=True, check=False
            )
            
            if result.returncode == 0:
                # Parse output and create Database objects
                lines = result.stdout.strip().split('\n')[1:]  # Skip header line
                databases = []
                
                for line in lines:
                    db_name = line.strip()
                    if db_name not in ['information_schema', 'performance_schema', 'mysql', 'sys']:
                        databases.append(Database(
                            name=db_name,
                            db_type='mysql',
                            size=0,  # We could get the actual size with another query
                            tables=0  # Same for tables
                        ))
                
                return databases
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        # Fallback: return empty list
        return []
    
    @classmethod
    def get_postgres_databases(cls):
        """Get a list of PostgreSQL databases"""
        try:
            # Try to execute the command to list PostgreSQL databases
            result = subprocess.run(
                ['psql', '-c', '\\l'],
                capture_output=True, text=True, check=False
            )
            
            if result.returncode == 0:
                # Parse output and create Database objects
                lines = result.stdout.strip().split('\n')
                databases = []
                
                # Very basic parsing - would need more robust parsing in production
                for line in lines:
                    if re.match(r'^\s+\w+\s+\|', line):
                        db_name = line.strip().split('|')[0].strip()
                        if db_name not in ['postgres', 'template0', 'template1']:
                            databases.append(Database(
                                name=db_name,
                                db_type='postgres',
                                size=0,
                                tables=0
                            ))
                
                return databases
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        # Fallback: return empty list
        return []
    
    @classmethod
    def create_mysql_database(cls, name, user=None, password=None):
        """Create a new MySQL database"""
        try:
            # Create database
            subprocess.run(
                ['mysql', '-e', f"CREATE DATABASE {name}"],
                check=False
            )
            
            # Create user and grant privileges if credentials provided
            if user and password:
                subprocess.run([
                    'mysql', '-e', 
                    f"CREATE USER '{user}'@'localhost' IDENTIFIED BY '{password}'; "
                    f"GRANT ALL PRIVILEGES ON {name}.* TO '{user}'@'localhost'; "
                    f"FLUSH PRIVILEGES;"
                ], check=False)
                
                # Store credentials
                next_id = max([cred.id for cred in cls._credentials], default=0) + 1
                cls._credentials.append(Credential(
                    id=next_id,
                    db_name=name,
                    db_type='mysql',
                    username=user,
                    password=password
                ))
            
            return True
        except subprocess.SubprocessError:
            return False
    
    @classmethod
    def create_postgres_database(cls, name, user=None, password=None):
        """Create a new PostgreSQL database"""
        try:
            # Create database
            subprocess.run(
                ['createdb', name],
                check=False
            )
            
            # Create user and grant privileges if credentials provided
            if user and password:
                # Create user if it doesn't exist
                subprocess.run([
                    'psql', '-c', 
                    f"CREATE USER {user} WITH ENCRYPTED PASSWORD '{password}'"
                ], check=False)
                
                # Grant privileges
                subprocess.run([
                    'psql', '-c', 
                    f"GRANT ALL PRIVILEGES ON DATABASE {name} TO {user}"
                ], check=False)
                
                # Store credentials
                next_id = max([cred.id for cred in cls._credentials], default=0) + 1
                cls._credentials.append(Credential(
                    id=next_id,
                    db_name=name,
                    db_type='postgres',
                    username=user,
                    password=password
                ))
            
            return True
        except subprocess.SubprocessError:
            return False
    
    @classmethod
    def get_all_credentials(cls):
        """Get all stored database credentials"""
        return cls._credentials
    
    @staticmethod
    def create_mysql_user(username, password, db_name=None, user_id=None):
        """Create a new MySQL user with optional database access"""
        try:
            conn = mysql.connector.connect(user='root', host='localhost')
            cursor = conn.cursor()
            
            # Create user with password
            cursor.execute(f"CREATE USER '{username}'@'%' IDENTIFIED BY '{password}'")
            
            # Grant privileges if a database is specified
            if db_name:
                cursor.execute(f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{username}'@'%'")
            
            cursor.execute("FLUSH PRIVILEGES")
            cursor.close()
            conn.close()
            
            # Save credentials in the database
            credential = DBCredential(
                db_type='mysql',
                username=username,
                password=password,
                database=db_name,
                created_by=user_id
            )
            db.session.add(credential)
            db.session.commit()
            
            return True
        except Exception as e:
            print(f"Error creating MySQL user: {str(e)}")
            return False
    
    @staticmethod
    def create_postgres_user(username, password, db_name=None, user_id=None):
        """Create a new PostgreSQL user with optional database access"""
        try:
            conn = psycopg2.connect(user='postgres', host='localhost')
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Create user with password
            cursor.execute(f"CREATE USER {username} WITH PASSWORD '{password}'")
            
            # Grant privileges if a database is specified
            if db_name:
                cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {username}")
            
            cursor.close()
            conn.close()
            
            # Save credentials in the database
            credential = DBCredential(
                db_type='postgres',
                username=username,
                password=password,
                database=db_name,
                created_by=user_id,
                port=5432
            )
            db.session.add(credential)
            db.session.commit()
            
            return True
        except Exception as e:
            print(f"Error creating PostgreSQL user: {str(e)}")
            return False
    
    @staticmethod
    def open_port(db_type):
        """Open the database port in UFW firewall"""
        try:
            if db_type == 'mysql':
                port = 3306
            elif db_type == 'postgres':
                port = 5432
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            subprocess.run(['sudo', 'ufw', 'allow', str(port)], check=True)
            return True
        except Exception as e:
            print(f"Error opening port: {str(e)}")
            return False
    
    @staticmethod
    def get_credential_by_id(credential_id):
        """Get a credential by ID"""
        return DBCredential.query.get(credential_id) 