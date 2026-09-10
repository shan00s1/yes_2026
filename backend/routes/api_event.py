"""
YES 2026 Summit - Event Metadata & Health APIs
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from database import get_event_meta, get_schedule_items, get_speakers_list, get_engine_status
from backend.config import ENVIRONMENT

event_api_bp = Blueprint("event_api", __name__)

@event_api_bp.route("/api/event/info")
def api_event_info():
    return jsonify({"success": True, "event": get_event_meta()})

@event_api_bp.route("/api/event/schedule")
def api_event_schedule():
    day = request.args.get("day", "day1")
    return jsonify({"success": True, "schedule": get_schedule_items(day)})

@event_api_bp.route("/api/event/speakers")
def api_event_speakers():
    return jsonify({"success": True, "speakers": get_speakers_list()})

@event_api_bp.route("/api/health")
def api_health():
    engine_status = get_engine_status()
    return jsonify({
        "status": "healthy" if engine_status.get("connected") else "degraded",
        "timestamp": datetime.now().isoformat(),
        "database": engine_status,
        "event": "YES 2026",
        "organizer": "VTU VRIF Belagavi",
        "environment": ENVIRONMENT
    })

@event_api_bp.route("/api/db-status")
def api_db_status():
    return jsonify(get_engine_status())
