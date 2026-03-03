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
            import json
            await send({
                'type': 'http.response.start',
                'status': 500,
                'headers': [[b'content-type', b'application/json']],
            })
            err_payload = json.dumps({
                "detail": "Vercel Import Error.",
                "traceback": err_msg
            }).encode()
            await send({
                'type': 'http.response.body',
                'body': err_payload,
            })
    app = err_app
