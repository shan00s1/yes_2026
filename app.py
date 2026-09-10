"""
YES 2026 Summit - Server & Vercel Entrypoint
VTU's Visvesvaraya Research and Innovation Foundation (VRIF), Belagavi
"""

import sys
import os
import traceback
from pathlib import Path

# Ensure workspace root is in python path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Safe bootstrap of the Flask application
try:
    from backend.app import app
except Exception as e:
    startup_tb = traceback.format_exc()
    print(f"[Startup Exception]:\n{startup_tb}", file=sys.stderr)
    from flask import Flask
    app = Flask(__name__)
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def startup_error(path):
        return f"""<!DOCTYPE html>
<html>
<body style="font-family: monospace; padding: 40px; background: #0b0f19; color: #f8fafc;">
  <div style="max-width: 800px; margin: 0 auto; background: #161e2e; border: 1px solid #ef4444; border-radius: 8px; padding: 24px;">
    <h2 style="color: #ef4444;">YES 2026 - Serverless Startup Error</h2>
    <pre style="background: #030712; padding: 16px; border-radius: 6px; color: #fca5a5; overflow-x: auto;">{startup_tb}</pre>
  </div>
</body>
</html>""", 500

from backend.config import SERVER_HOST, SERVER_PORT

# WSGI Middleware to restore clean request path and catch runtime exceptions
class VercelWSGIHandler:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # Restore clean path from Vercel edge rewrite
        matched = environ.get('HTTP_X_MATCHED_PATH') or environ.get('HTTP_X_FORWARDED_URI')
        if matched and not matched.startswith('/app.py'):
            environ['PATH_INFO'] = matched.split('?')[0]
            environ['REQUEST_URI'] = matched

        try:
            return self.wsgi_app(environ, start_response)
        except Exception:
            err_tb = traceback.format_exc()
            print(f"[Vercel Runtime Request Error]:\n{err_tb}", file=sys.stderr)
            status = '500 Internal Server Error'
            headers = [('Content-type', 'text/html; charset=utf-8')]
            start_response(status, headers)
            body = f"""<!DOCTYPE html>
<html>
<body style="font-family: monospace; padding: 40px; background: #0b0f19; color: #f8fafc;">
  <div style="max-width: 800px; margin: 0 auto; background: #161e2e; border: 1px solid #f97316; border-radius: 8px; padding: 24px;">
    <h2 style="color: #f97316;">YES 2026 - Runtime Exception</h2>
    <pre style="background: #030712; padding: 16px; border-radius: 6px; color: #fdba74; overflow-x: auto;">{err_tb}</pre>
  </div>
</body>
</html>"""
            return [body.encode('utf-8')]

app.wsgi_app = VercelWSGIHandler(app.wsgi_app)

# Expose aliases for Vercel
application = app
handler = app

if __name__ == "__main__":
    from database import get_engine_status
    status = get_engine_status()
    engine_name = status.get("engine", "Supabase Cloud")

    print("\n" + "=" * 75)
    print("   YOUNG ENTREPRENEURS SUMMIT - YES 2026 | VTU VRIF BELAGAVI")
    print(f"   Database Engine: {engine_name}")
    print("=" * 75)
    print("   [PRIMARY WEB ACCESS - ZERO PRIVACY WARNINGS]:")
    print("    >> Landing Page:      http://localhost:5000/")
    print("    >> Registration:      http://localhost:5000/register")
    print("    >> Scanner Kiosk:     http://localhost:5000/checkin")
    print("    >> Admin Console:     http://localhost:5000/admin")
    print("    >> Health Check API:  http://localhost:5000/api/health")
    print("=" * 75 + "\n")

    if "--production" in sys.argv:
        try:
            from waitress import serve
            print(" * [Production WSGI] Serving with Waitress multi-threaded production server on port 5000...")
            serve(app, host=SERVER_HOST, port=SERVER_PORT, threads=8)
        except ImportError:
            app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False)
    else:
        app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False)
