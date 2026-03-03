import os
import sys

# Prevent Vercel read-only filesystem errors for cache dirs
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"
os.environ["YFINANCE_CACHE_DIR"] = "/tmp/yfinance"
os.environ["XDG_CACHE_HOME"] = "/tmp/cache"

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Catch import errors directly on Vercel boot
try:
    from backend.main import app
except Exception as e:
    import traceback
    err_msg = traceback.format_exc()
    
    async def err_app(scope, receive, send):
        if scope['type'] == 'http':
            await send({
                'type': 'http.response.start',
                'status': 500,
                'headers': [[b'content-type', b'text/plain']],
            })
            await send({
                'type': 'http.response.body',
                'body': f"Vercel Import Error:\n{err_msg}".encode(),
            })
    app = err_app
