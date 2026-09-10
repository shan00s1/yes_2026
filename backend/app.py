"""
YES 2026 Summit - Flask Application Factory & Core Server
VTU's Visvesvaraya Research and Innovation Foundation (VRIF), Belagavi
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask, request, jsonify, redirect

BASE_DIR = Path(__file__).resolve().parent.parent
# Ensure workspace root is in sys.path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config import SECRET_KEY, ENVIRONMENT
from backend.routes import pages_bp, attendees_bp, admin_api_bp, event_api_bp
from database import init_db

logger = logging.getLogger("yes2026.app")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def create_app():
    current_cwd = Path.cwd()
    templates_dir = None
    for candidate in [
        BASE_DIR / "frontend" / "templates",
        current_cwd / "frontend" / "templates",
        BASE_DIR / "templates",
        current_cwd / "templates"
    ]:
        if candidate.exists():
            templates_dir = str(candidate)
            break
    if not templates_dir:
        templates_dir = str(BASE_DIR / "frontend" / "templates")

    static_dir = None
    for candidate in [
        BASE_DIR / "frontend" / "static",
        current_cwd / "frontend" / "static",
        BASE_DIR / "static",
        current_cwd / "static"
    ]:
        if candidate.exists():
            static_dir = str(candidate)
            break
    if not static_dir:
        static_dir = str(BASE_DIR / "frontend" / "static")

    app = Flask(
        __name__,
        template_folder=templates_dir,
        static_folder=static_dir
    )
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["JSON_SORT_KEYS"] = False
    app.config["TEMPLATES_AUTO_RELOAD"] = True

    # Security & Production Headers
    @app.after_request
    def apply_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    # Global Error Handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "error": "API endpoint not found", "path": request.path}), 404
        return redirect("/")

    @app.errorhandler(500)
    def handle_internal_error(e):
        logger.error(f"Internal server error: {e}", exc_info=True)
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "error": "Internal server error", "details": str(e)}), 500
        return "<h3>Internal Server Error - YES 2026</h3>", 500

    # Register Blueprints
    app.register_blueprint(pages_bp)
    app.register_blueprint(attendees_bp)
    app.register_blueprint(admin_api_bp)
    app.register_blueprint(event_api_bp)

    # Initialize DB check
    try:
        init_db(clean_dummy_data=False)
    except Exception as ex:
        logger.warning(f"Database init notice: {ex}")

    return app

app = create_app()
