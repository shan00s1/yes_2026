"""
YES 2026 Summit - Unified Database Package
VTU's Visvesvaraya Research and Innovation Foundation (VRIF), Belagavi
"""

import time
import json
import logging
from datetime import datetime
from backend.config import SUPABASE_URL, SUPABASE_KEY, DATABASE_URL
from database import supabase_client
from database.connection import USE_POSTGRES, IS_SUPABASE, get_connection

from pathlib import Path

logger = logging.getLogger("yes2026.database")

_CACHE_FILE = Path(__file__).resolve().parent / "registrations_cache.json"

# In-memory buffer for zero-downtime operation before table creation on Supabase
_MEM_REGISTRATIONS = {}
_MEM_EMAILS = []
_MEM_ACTIVITIES = []

def _load_cache():
    global _MEM_REGISTRATIONS
    if _CACHE_FILE.exists():
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _MEM_REGISTRATIONS.update(data)
                    logger.info(f"[Database Cache] Loaded {len(_MEM_REGISTRATIONS)} cached registrations.")
        except Exception as e:
            logger.warning(f"[Database Cache] Notice reading cache: {e}")

def _save_cache():
    try:
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_MEM_REGISTRATIONS, f, indent=2)
    except Exception as e:
        logger.warning(f"[Database Cache] Notice writing cache: {e}")

_load_cache()

def is_supabase_cloud_active() -> bool:
    """Returns True if Supabase REST API has tables ready and active."""
    return supabase_client.is_table_available("registrations")

# ----------------- UNIFIED DATA REPOSITORY API ----------------- #

def create_registration(data: dict) -> dict:
    if is_supabase_cloud_active():
        return supabase_client.create_registration(data)

    # In-memory zero-downtime fallback
    category = data.get("category", "participant").strip().lower()
    if category == "vip":
        category = "faculty"
    reg_id = supabase_client.generate_registration_id(category)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    custom_fields = data.get("custom_fields", {})
    record = {
        "id": len(_MEM_REGISTRATIONS) + 1,
        "registration_id": reg_id,
        "category": category,
        "full_name": data.get("full_name", "").strip(),
        "email": data.get("email", "").strip().lower(),
        "phone": data.get("phone", "").strip(),
        "organization": data.get("organization", "").strip(),
        "designation": data.get("designation", "").strip() or ("Student / Innovator" if category == "participant" else ("Professor / Academician" if category == "faculty" else "Executive")),
        "track_or_industry": data.get("track_or_industry", "").strip() or "General Innovation Track",
        "custom_fields": custom_fields,
        "custom_fields_json": json.dumps(custom_fields) if isinstance(custom_fields, dict) else str(custom_fields),
        "qr_code_data": reg_id,
        "status": "REGISTERED",
        "check_in_time": None,
        "check_in_station": None,
        "created_at": now_str,
        "email_sent": 1
    }
    _MEM_REGISTRATIONS[reg_id] = record
    _save_cache()
    return record

def get_registration_by_id(reg_id: str):
    if is_supabase_cloud_active():
        return supabase_client.get_registration_by_id(reg_id)
    cleaned = (reg_id or "").strip().upper()
    if cleaned not in _MEM_REGISTRATIONS:
        _load_cache()
    return _MEM_REGISTRATIONS.get(cleaned)

def get_registration_by_email(email: str):
    if is_supabase_cloud_active():
        found = supabase_client.get_registration_by_email(email)
        if found:
            return found
    cleaned = (email or "").strip().lower()
    if not cleaned:
        return None
    _load_cache()
    for r in _MEM_REGISTRATIONS.values():
        if (r.get("email") or "").strip().lower() == cleaned:
            return r
    return None

def check_in_attendee(code: str, station: str = "Gate 1 Check-in Kiosk") -> dict:
    if is_supabase_cloud_active():
        return supabase_client.check_in_attendee(code, station)

    cleaned = (code or "").strip().upper()
    if cleaned not in _MEM_REGISTRATIONS:
        _load_cache()

    attendee = _MEM_REGISTRATIONS.get(cleaned)
    if not attendee:
        for r in _MEM_REGISTRATIONS.values():
            if r.get("email") == (code or "").strip().lower():
                attendee = r
                break

    if not attendee:
        return {"success": False, "error_type": "NOT_FOUND", "message": f"Registration '{code}' not found."}

    if attendee.get("status") == "CHECKED_IN":
        return {
            "success": False,
            "error_type": "DUPLICATE",
            "message": f"Attendee already checked in at {attendee.get('check_in_time')} ({attendee.get('check_in_station')}). Duplicate entry denied.",
            "attendee": attendee,
            "check_in_time": attendee.get("check_in_time"),
            "check_in_station": attendee.get("check_in_station")
        }

    now_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    attendee["status"] = "CHECKED_IN"
    attendee["check_in_time"] = now_str
    attendee["check_in_station"] = station
    _save_cache()

    return {
        "success": True,
        "message": f"Verification successful. Welcome, {attendee['full_name']}!",
        "attendee": attendee,
        "check_in_time": now_str,
        "check_in_station": station
    }

def toggle_checkin_status(reg_id: str) -> dict:
    if is_supabase_cloud_active():
        return supabase_client.toggle_checkin_status(reg_id)

    attendee = _MEM_REGISTRATIONS.get(reg_id)
    if not attendee:
        return {"success": False, "error": "Registration not found."}

    if attendee.get("status") == "CHECKED_IN":
        attendee["status"] = "REGISTERED"
        attendee["check_in_time"] = None
        attendee["check_in_station"] = None
        _save_cache()
        return {"success": True, "new_status": "REGISTERED", "message": "Check-in undone."}
    else:
        now_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        attendee["status"] = "CHECKED_IN"
        attendee["check_in_time"] = now_str
        attendee["check_in_station"] = "Admin Manual Override"
        _save_cache()
        return {"success": True, "new_status": "CHECKED_IN", "message": "Manual check-in confirmed."}

def update_registration(reg_id: str, updates: dict) -> dict:
    if is_supabase_cloud_active():
        return supabase_client.update_registration(reg_id, updates)

    attendee = _MEM_REGISTRATIONS.get(reg_id)
    if not attendee:
        return {"success": False, "error": "Registration not found."}

    allowed = ["full_name", "email", "phone", "organization", "designation", "track_or_industry"]
    for k in allowed:
        if k in updates:
            attendee[k] = updates[k].strip()
    _save_cache()

    return {"success": True, "attendee": attendee}

def delete_registration(reg_id: str) -> bool:
    if is_supabase_cloud_active():
        return supabase_client.delete_registration(reg_id)
    _MEM_REGISTRATIONS.pop(reg_id, None)
    _save_cache()
    return True

def clear_all_attendees() -> bool:
    if is_supabase_cloud_active():
        supabase_client.clear_all_attendees()
    _MEM_REGISTRATIONS.clear()
    _MEM_EMAILS.clear()
    _MEM_ACTIVITIES.clear()
    _save_cache()
    return True

def get_registrations(search: str = "", category: str = "", status: str = "", limit: int = 100, offset: int = 0) -> dict:
    if is_supabase_cloud_active():
        return supabase_client.get_registrations(search, category, status, limit, offset)

    rows = list(_MEM_REGISTRATIONS.values())
    if search:
        s = search.strip().lower()
        rows = [r for r in rows if s in r.get("full_name", "").lower() or s in r.get("email", "").lower() or s in r.get("registration_id", "").lower()]
    if category and category.lower() != "all":
        rows = [r for r in rows if r.get("category") == category.lower()]
    if status and status.upper() != "ALL":
        rows = [r for r in rows if r.get("status") == status.upper()]

    total = len(rows)
    paged = rows[offset:offset + limit]
    return {"total": total, "registrations": paged, "limit": limit, "offset": offset}

def get_dashboard_stats() -> dict:
    if is_supabase_cloud_active():
        return supabase_client.get_dashboard_stats()

    rows = list(_MEM_REGISTRATIONS.values())
    total = len(rows)
    checked = sum(1 for r in rows if r.get("status") == "CHECKED_IN")
    pending = max(0, total - checked)
    rate = round((checked / total * 100), 1) if total > 0 else 0.0

    cats = {"participant": 0, "delegate": 0, "faculty": 0}
    for r in rows:
        c = (r.get("category") or "").lower()
        if c == "vip":
            c = "faculty"
        if c in cats:
            cats[c] += 1

    return {
        "total": total,
        "checked_in": checked,
        "pending": pending,
        "attendance_rate": rate,
        "categories": cats
    }

def get_recent_checkins(limit: int = 15) -> list:
    if is_supabase_cloud_active():
        return supabase_client.get_recent_checkins(limit)

    checked = [r for r in _MEM_REGISTRATIONS.values() if r.get("status") == "CHECKED_IN"]
    return sorted(checked, key=lambda x: x.get("check_in_time") or "", reverse=True)[:limit]

def log_email(reg_id: str, recipient: str, subject: str, html_body: str):
    if is_supabase_cloud_active():
        supabase_client.log_email(reg_id, recipient, subject, html_body)
    now_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    _MEM_EMAILS.append({"registration_id": reg_id, "recipient_email": recipient, "subject": subject, "html_body": html_body, "sent_at": now_str})

def get_latest_email(reg_id: str):
    if is_supabase_cloud_active():
        return supabase_client.get_latest_email(reg_id)
    for e in reversed(_MEM_EMAILS):
        if e.get("registration_id") == reg_id:
            return e
    return None

def log_activity(reg_id: str, action: str, details: str):
    if is_supabase_cloud_active():
        supabase_client.log_activity(reg_id, action, details)
    _MEM_ACTIVITIES.append({"registration_id": reg_id, "action": action, "details": details, "timestamp": datetime.now().isoformat()})

def get_event_meta() -> dict:
    return supabase_client.get_event_meta()

def get_schedule_items(day: str = "day1") -> list:
    return supabase_client.get_schedule_items(day)

def get_speakers_list() -> list:
    return supabase_client.get_speakers_list()

def init_db(clean_dummy_data=True):
    logger.info("[Database] Initialized cloud database interface.")

def get_db():
    return None

def ping_database() -> dict:
    t0 = time.perf_counter()
    table_ready = is_supabase_cloud_active()
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "healthy": True,
        "latency_ms": latency_ms,
        "table_ready": table_ready,
        "engine": "Supabase Cloud (Active)" if table_ready else "Supabase Cloud (Pending Table Creation)",
        "is_supabase": True
    }

def get_engine_status() -> dict:
    ping_info = ping_database()
    return {
        "connected": ping_info.get("healthy", False),
        "engine": ping_info.get("engine", "Supabase Cloud"),
        "latency_ms": ping_info.get("latency_ms"),
        "is_supabase": True,
        "is_postgres": USE_POSTGRES,
        "database_url_configured": bool(DATABASE_URL),
        "supabase_cloud": {
            "configured": bool(SUPABASE_URL and SUPABASE_KEY),
            "table_exists": ping_info.get("table_ready", False),
            "project_url": SUPABASE_URL
        }
    }
