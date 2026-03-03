import os
import sys

# Define the absolute path to the backend directory
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Now import the app directly from main
from main import app
