"""
YES 2026 Summit - Server Entrypoint
VTU's Visvesvaraya Research and Innovation Foundation (VRIF), Belagavi

Entrypoint for:
- Local development & production: python app.py
- Vercel Serverless Function: exposes 'app'
"""

import sys
import os

# Ensure workspace root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app
from backend.config import SERVER_HOST, SERVER_PORT
from database import get_engine_status

if __name__ == "__main__":
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
