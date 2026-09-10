"""
YES 2026 Summit - Production WSGI Application Entrypoint
VTU's Visvesvaraya Research and Innovation Foundation (VRIF), Belagavi

Used by production WSGI servers:
- Windows: Waitress (python wsgi.py or waitress-serve --port=5000 wsgi:application)
- Linux / Containers / PaaS: Gunicorn (gunicorn wsgi:application -w 4 -b 0.0.0.0:5000)
"""

import sys
import os
import logging

# Ensure root workspace directory is in Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app as application
from backend.config import SERVER_HOST, SERVER_PORT, ENVIRONMENT

logger = logging.getLogger("yes2026.wsgi")

if __name__ == "__main__":
    try:
        from waitress import serve
        print("=" * 75)
        print("  YES 2026 SUMMIT - PRODUCTION WSGI SERVER (WAITRESS)")
        print("  VTU's Visvesvaraya Research and Innovation Foundation (VRIF)")
        print(f"  Listening at: http://{SERVER_HOST}:{SERVER_PORT}")
        print("  Environment: Production (Multi-Threaded WSGI)")
        print("=" * 75)
        serve(application, host=SERVER_HOST, port=SERVER_PORT, threads=8)
    except ImportError:
        print("[!] Waitress not found, falling back to standard server.")
        application.run(host=SERVER_HOST, port=SERVER_PORT, debug=False)
