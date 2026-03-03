import os
import sys

# Add the 'backend' folder to the Python path so imports like 'from database import...' work
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

# Import the FastAPI 'app' from main.py inside backend/
from main import app
