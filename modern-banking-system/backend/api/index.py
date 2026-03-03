import os
import sys

# Vercel Serverless Function entry point
# Add the backend directory to sys.path so the module imports work correctly
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from main import app
