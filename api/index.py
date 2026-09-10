"""
YES 2026 Summit - Vercel Serverless Entrypoint & Edge Handler
VTU's Visvesvaraya Research and Innovation Foundation (VRIF), Belagavi
"""

import sys
import os
import traceback
import urllib.parse
from pathlib import Path

# Ensure workspace root is in python module search path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Safe bootstrap of the Flask application
try:
    from backend.app import app as flask_app
    _BOOTSTRAP_ERROR = None
except Exception as e:
    flask_app = None
    _BOOTSTRAP_ERROR = traceback.format_exc()
    print(f"[Vercel Startup Error]:\n{_BOOTSTRAP_ERROR}", file=sys.stderr)


def _resolve_request_path(environ):
    """
    Extracts the user's actual requested path when Vercel rewrites the request
    to /api/index.py. Checks all headers injected by Vercel edge.
    """
    path = environ.get("PATH_INFO", "/")
    
    # Only override if PATH_INFO points to the serverless entrypoint itself
    if path in ("/api/index.py", "/api/index", "/api", "/index.py"):
        # 1. Edge forwarded URI (e.g. /register?category=delegate)
        fwd_uri = (
            environ.get("HTTP_X_FORWARDED_URI")
            or environ.get("HTTP_X_VERCEL_FORWARDED_PATH")
            or environ.get("HTTP_X_ORIGINAL_URI")
        )
        if fwd_uri:
            clean = fwd_uri.split("?")[0]
            if clean and not clean.startswith("/api/index"):
                return clean

        # 2. Vercel route regex matches (e.g. 1=%2Fregister)
        route_matches = environ.get("HTTP_X_NOW_ROUTE_MATCHES", "")
        if route_matches:
            try:
                parsed = urllib.parse.parse_qs(route_matches)
                if "1" in parsed and parsed["1"]:
                    matched = parsed["1"][0]
                    if not matched.startswith("/"):
                        matched = "/" + matched
                    return matched
            except Exception:
                pass

        # 3. Matched path header
        matched_path = environ.get("HTTP_X_MATCHED_PATH", "")
        if matched_path and not matched_path.startswith("/api/index"):
            return matched_path.split("?")[0]

        # 4. Standard root request
        return "/"

    return path


class VercelEdgeWSGI:
    """
    WSGI wrapper ensuring:
    - Accurate path routing from Vercel edge rewrites
    - Zero unhandled crash containment (prevents FUNCTION_INVOCATION_FAILED)
    - Clean diagnostic visibility if startup fails
    """
    def __init__(self, app, bootstrap_err=None):
        self.app = app
        self.bootstrap_err = bootstrap_err

    def __call__(self, environ, start_response):
        # If bootstrap failed, render diagnostic page instead of crashing Lambda
        if self.bootstrap_err or self.app is None:
            err_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>YES 2026 - Server Initialization Error</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0b0f19; color: #f8fafc; padding: 40px 20px; }}
    .box {{ max-width: 820px; margin: 0 auto; background: #111827; border: 1px solid #ef4444; border-radius: 12px; padding: 32px; }}
    h1 {{ color: #ef4444; font-size: 22px; margin-top: 0; }}
    pre {{ background: #030712; padding: 18px; border-radius: 8px; overflow-x: auto; color: #fca5a5; font-size: 13px; line-height: 1.5; }}
  </style>
</head>
<body>
  <div class="box">
    <h1>YES 2026 Summit - Startup Diagnostic Notice</h1>
    <p>A module initialization error occurred while starting the application on Vercel:</p>
    <pre>{self.bootstrap_err or 'Unknown initialization error'}</pre>
    <p style="color: #94a3b8; font-size: 13px;">Please verify your environment variables in Vercel Project Settings.</p>
  </div>
</body>
</html>"""
            data = err_html.encode("utf-8")
            start_response("500 Internal Server Error", [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(data)))
            ])
            return [data]

        # Resolve the true requested route
        real_path = _resolve_request_path(environ)
        environ["PATH_INFO"] = real_path
        environ["REQUEST_URI"] = real_path

        try:
            return self.app(environ, start_response)
        except Exception as runtime_err:
            tb = traceback.format_exc()
            print(f"[Vercel Runtime Exception]:\n{tb}", file=sys.stderr)
            err_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>YES 2026 - Application Runtime Error</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0b0f19; color: #f8fafc; padding: 40px 20px; }}
    .box {{ max-width: 820px; margin: 0 auto; background: #111827; border: 1px solid #f59e0b; border-radius: 12px; padding: 32px; }}
    h1 {{ color: #f59e0b; font-size: 22px; margin-top: 0; }}
    pre {{ background: #030712; padding: 18px; border-radius: 8px; overflow-x: auto; color: #fde68a; font-size: 13px; line-height: 1.5; }}
  </style>
</head>
<body>
  <div class="box">
    <h1>YES 2026 Summit - Runtime Notice</h1>
    <p>An exception was encountered while serving route: <code>{real_path}</code></p>
    <pre>{tb}</pre>
  </div>
</body>
</html>"""
            data = err_html.encode("utf-8")
            start_response("500 Internal Server Error", [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(data)))
            ])
            return [data]


# Primary WSGI callable for Vercel Python Runtime
app = VercelEdgeWSGI(flask_app, _BOOTSTRAP_ERROR)
handler = app
