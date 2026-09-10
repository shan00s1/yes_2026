"""
YES 2026 Summit - Vercel Serverless Function Entrypoint
VTU's Visvesvaraya Research and Innovation Foundation (VRIF), Belagavi
"""

import os
import sys
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Expose WSGI application object for Vercel
from backend.app import app

# Handler alias for Vercel Python runtime
handler = app
app = app
