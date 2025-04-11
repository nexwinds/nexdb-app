"""
NEXDB - Entry Point
Run with: flask run (development) or gunicorn app:app (production)
"""

import os
from app import create_app

# Create the Flask application instance
app = create_app(os.getenv('FLASK_CONFIG', 'default'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 