import os
import sys
from dotenv import load_dotenv

# Add application directory to path
sys.path.insert(0, '/var/www/html/ictaz_info_collector')

# Load environment variables
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Create upload folder before importing app
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(basedir, 'static', 'uploads'))
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except Exception as e:
    print(f"Error creating upload folder: {e}")

# Import application
from app import app as application

if __name__ == "__main__":
    application.run()
