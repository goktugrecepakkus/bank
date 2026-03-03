import os
import sys

# In Vercel, the root is the project root. Add `backend` to sys.path so modules like `database` load properly.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from main import app
