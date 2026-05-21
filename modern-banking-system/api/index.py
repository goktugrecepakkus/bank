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

# Vercel statik kod analizinin "app" değişkenini rahatça bulabilmesi için ASGI wrapper
async def app(scope, receive, send):
    try:
        from backend.main import app as real_app
        await real_app(scope, receive, send)
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        if scope['type'] == 'http':
            import json
            await send({
                'type': 'http.response.start',
                'status': 500,
                'headers': [[b'content-type', b'application/json']],
            })
            err_payload = json.dumps({
                "detail": f"Vercel Runtime Crash: {str(e)}",
                "traceback": err_msg
            }).encode()
            await send({
                'type': 'http.response.body',
                'body': err_payload,
            })
