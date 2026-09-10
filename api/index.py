"""
YES 2026 Summit - Vercel Serverless Function Entrypoint
VTU's Visvesvaraya Research and Innovation Foundation (VRIF), Belagavi
"""

import os
import sys
import traceback
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Safe bootstrap of the Flask application
try:
    from backend.app import app
except Exception as init_err:
    startup_tb = traceback.format_exc()
    print(f"[Vercel Startup Critical Error]:\n{startup_tb}", file=sys.stderr)
    from flask import Flask
    app = Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def fallback_crash_handler(path):
        return f"""<!DOCTYPE html>
<html>
<head><title>YES 2026 - Deployment Initialization Error</title></head>
<body style="font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; background: #090d16; color: #f8fafc; padding: 40px;">
  <div style="max-width: 800px; margin: 0 auto; background: #111827; border: 1px solid #ef4444; border-radius: 12px; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
    <h2 style="color: #ef4444; margin-top: 0;">⚠️ Serverless Function Startup Error</h2>
    <p style="color: #94a3b8;">The Python application encountered an error during import initialization on Vercel:</p>
    <pre style="background: #030712; padding: 16px; border-radius: 8px; color: #fca5a5; overflow-x: auto; font-size: 13px; line-height: 1.5;">{startup_tb}</pre>
    <p style="color: #64748b; font-size: 12px; margin-bottom: 0;">Check your Vercel Project Settings &gt; Environment Variables or Deploy Logs.</p>
  </div>
</body>
</html>""", 500

# Error-catching & path-restoring WSGI middleware for Vercel
class VercelWSGIMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # Restore original path from Vercel edge rewrite headers
        orig_path = environ.get('HTTP_X_MATCHED_PATH') or environ.get('HTTP_X_FORWARDED_URI')
        if orig_path and not orig_path.startswith('/api/index'):
            clean_path = orig_path.split('?')[0]
            environ['PATH_INFO'] = clean_path
            environ['REQUEST_URI'] = orig_path

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
<head><title>YES 2026 - Runtime Exception</title></head>
<body style="font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; background: #090d16; color: #f8fafc; padding: 40px;">
  <div style="max-width: 800px; margin: 0 auto; background: #111827; border: 1px solid #f97316; border-radius: 12px; padding: 24px;">
    <h2 style="color: #f97316; margin-top: 0;">⚠️ Serverless Runtime Exception</h2>
    <pre style="background: #030712; padding: 16px; border-radius: 8px; color: #fdba74; overflow-x: auto; font-size: 13px;">{err_tb}</pre>
  </div>
</body>
</html>"""
            return [body.encode('utf-8')]

app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
handler = app
