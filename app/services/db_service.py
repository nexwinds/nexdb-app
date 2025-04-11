import subprocess
import re
import mysql.connector
import psycopg2
from app.models import db
from app.models.db_credential import DBCredential

class DBService:
    @staticmethod
    def get_mysql_databases():
        """Get a list of MySQL databases"""
        try:
            conn = mysql.connector.connect(user='root', host='localhost')
            cursor = conn.cursor()
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall() if db[0] not in ['information_schema', 'performance_schema', 'mysql', 'sys']]
            cursor.close()
            conn.close()
            return databases
        except Exception as e:
            print(f"Error getting MySQL databases: {str(e)}")
            return []
    
    @staticmethod
    def get_postgres_databases():
        """Get a list of PostgreSQL databases"""
        try:
            conn = psycopg2.connect(user='postgres', host='localhost')
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false AND datname != 'postgres'")
            databases = [db[0] for db in cursor.fetchall()]
            cursor.close()
            conn.close()
            return databases
        except Exception as e:
            print(f"Error getting PostgreSQL databases: {str(e)}")
            return []
    
    @staticmethod
    def create_mysql_database(db_name):
        """Create a new MySQL database"""
        try:
            conn = mysql.connector.connect(user='root', host='localhost')
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE {db_name}")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating MySQL database: {str(e)}")
            return False
    
    @staticmethod
    def create_postgres_database(db_name):
        """Create a new PostgreSQL database"""
        try:
            conn = psycopg2.connect(user='postgres', host='localhost')
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE {db_name}")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating PostgreSQL database: {str(e)}")
            return False
    
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
    def get_all_credentials():
        """Get all database credentials"""
        return DBCredential.query.order_by(DBCredential.created_at.desc()).all()
    
    @staticmethod
    def get_credential_by_id(credential_id):
        """Get a credential by ID"""
        return DBCredential.query.get(credential_id) 