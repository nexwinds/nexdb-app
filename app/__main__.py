# Fix for correctly importing the run_app function
import os
import sys

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import run_app from app
from app import run_app

if __name__ == '__main__':
    run_app() 