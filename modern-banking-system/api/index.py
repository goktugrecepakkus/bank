import os
import sys

# Prevent Vercel read-only filesystem errors for cache dirs
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"
os.environ["YFINANCE_CACHE_DIR"] = "/tmp/yfinance"
os.environ["XDG_CACHE_HOME"] = "/tmp/cache"

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
backend_dir = os.path.abspath(os.path.join(root_dir, 'backend'))

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Load .env before importing backend (Vercel uses dashboard env vars, this is a safety net)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(root_dir, "backend", ".env"))
except ImportError:
    pass

# Vercel statik kod analizinin "app" değişkenini rahatça bulabilmesi için try-except kullanmıyoruz
from backend.main import app
