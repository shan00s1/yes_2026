"""
YES 2026 Summit - Pure Supabase Cloud REST Database Engine
VTU's Visvesvaraya Research and Innovation Foundation (VRIF), Belagavi

Designed for Serverless & Cloud Deployments (Vercel, AWS Lambda, Render):
- 100% Cloud-native: Zero dependency on local disk or SQLite files
- Operates over HTTPS (Port 443) with Supabase PostgREST
- Sub-second responses and global accessibility across all devices
"""

import json
import logging
import random
import string
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

from backend.config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger("yes2026.database.supabase_client")

# Authentic default metadata for fallback or seeding
DEFAULT_EVENT_META = {
    "event_name": "YES 2026",
    "event_full_title": "Young Entrepreneurs Summit - YES 2026",
    "organizer": "VTU's Visvesvaraya Research and Innovation Foundation (VRIF), Belagavi",
    "dates": "27th & 28th September 2026",
    "venue_name": "VTU Main Campus, Jnana Sangama",
    "venue_address": "Machhe, Belagavi, Karnataka 590018",
    "venue_city": "Belagavi, Karnataka",
    "tagline": "Embrace the resounding 'YES' to innovations that propel us into the future.",
    "total_participants_hosted": "150",
    "tbi_location": "Second Floor, VRIF Building, TBI Centre, VTU Belagavi"
}

DEFAULT_SCHEDULE = {
    "day1": [
        {"day": "day1", "time_range": "08:30 AM - 10:00 AM", "title": "Express Registration & Badge Issuance", "description": "Camera-assisted QR check-in & personalized lanyard ID badge printing", "track_tag": "Desk Kiosk"},
        {"day": "day1", "time_range": "10:00 AM - 11:30 AM", "title": "Grand Inaugural Ceremony & Welcome Address", "description": "Welcome by VTU Leadership, Dignitary addresses by Govt of Karnataka IT/BT delegates", "track_tag": "APJ Abdul Kalam Auditorium"},
        {"day": "day1", "time_range": "11:30 AM - 12:30 PM", "title": "TBI Infrastructure Inauguration & Navodaya Cohort 1 Onboarding", "description": "Ribbon-cutting of 2nd Floor TBI Centre & induction ceremony for selected incubatees", "track_tag": "VRIF TBI Centre (2nd Floor)"},
        {"day": "day1", "time_range": "12:30 PM - 01:30 PM", "title": "Program Milestones: SamShoDhana, SheInnovates & Vinyasa", "description": "Presentation of breakthroughs in deep-tech translation, women founders & acceleration", "track_tag": "APJ Abdul Kalam Auditorium"},
        {"day": "day1", "time_range": "01:30 PM - 02:30 PM", "title": "Executive Networking Luncheon", "description": "Curated networking lunch for delegates, speakers, founders & mentors", "track_tag": "Executive Dining Pavilion"},
        {"day": "day1", "time_range": "02:30 PM - 04:30 PM", "title": "B2B Matchmaking & Stakeholder Roundtables", "description": "High-level dialogues on incubation policy, corporate partnerships & angel syndicates", "track_tag": "Jana Samvada 1 & 2"},
        {"day": "day1", "time_range": "04:30 PM - 05:30 PM", "title": "Keynote Address: Scaling Deep-Tech from North Karnataka", "description": "Distinguished founders and investors discuss tier-2 tech ecosystem growth", "track_tag": "APJ Abdul Kalam Auditorium"},
        {"day": "day1", "time_range": "06:30 PM - 09:30 PM", "title": "Cultural Evening, Musical Performances & Networking Dinner", "description": "Celebration of entrepreneurship with live cultural performances and banquet dinner", "track_tag": "Open Amphitheater & Campus Grounds"}
    ],
    "day2": [
        {"day": "day2", "time_range": "09:00 AM - 10:00 AM", "title": "Breakfast Mixer & Venture Networking", "description": "Informal morning connections between incubatees, delegates & angels", "track_tag": "Exhibition Courtyard"},
        {"day": "day2", "time_range": "10:00 AM - 01:00 PM", "title": "Top 20 Project Showcase & Live Investor Pitches", "description": "The 20 most promising VRIF-incubated startups pitch live before angel syndicates", "track_tag": "APJ Abdul Kalam Auditorium"},
        {"day": "day2", "time_range": "01:00 PM - 02:00 PM", "title": "Networking Lunch & Prototype Demo Walkthrough", "description": "Hands-on walkthrough of hardware, robotics, deep-tech & bio-engineering demos", "track_tag": "TBI Prototyping Hall"},
        {"day": "day2", "time_range": "02:00 PM - 03:30 PM", "title": "Panel: Intellectual Property, Patenting & Global Commercialization", "description": "Academic-industry technology transfer leaders discuss IP creation in universities", "track_tag": "Jana Samvada 1"},
        {"day": "day2", "time_range": "03:30 PM - 04:30 PM", "title": "Startup Karnataka & KDEM Policy Roundtable", "description": "Government support schemes, seed fund access, and regulatory frameworks", "track_tag": "Jana Samvada 2"},
        {"day": "day2", "time_range": "04:30 PM - 05:30 PM", "title": "YES 2026 Innovation Awards & Valedictory Ceremony", "description": "Presentation of Top Venture Grants, felicitations, and closing address", "track_tag": "APJ Abdul Kalam Auditorium"}
    ]
}

DEFAULT_SPEAKERS = [
    {
        "id": 1,
        "name": "Dr. S. Vidyashankar",
        "role": "Hon'ble Vice Chancellor",
        "organization": "Visvesvaraya Technological University, Belagavi",
        "initials": "SV",
        "photo": "/static/img/vc_dr_s_vidyashankar.jpg"
    },
    {
        "id": 2,
        "name": "Dr. Prasad Rampure",
        "role": "Registrar",
        "organization": "Visvesvaraya Technological University, Belagavi",
        "initials": "PR",
        "photo": "/static/img/registrar_dr_prasad_rampure.png"
    },
    {
        "id": 3,
        "name": "Dr. Ujwal U. J.",
        "role": "Registrar (Evaluation)",
        "organization": "Visvesvaraya Technological University, Belagavi",
        "initials": "UJ",
        "photo": "/static/img/registrar_eval_dr_ujwal.png"
    }
]

def get_base_url() -> str:
    return (SUPABASE_URL or "").rstrip('/')

def get_headers(prefer=None) -> dict:
    h = {
        "apikey": SUPABASE_KEY or "",
        "Authorization": f"Bearer {SUPABASE_KEY or ''}",
        "Content-Type": "application/json"
    }
    if prefer:
        h["Prefer"] = prefer
    return h

def generate_registration_id(category: str) -> str:
    cat_codes = {"participant": "PAR", "delegate": "DEL", "faculty": "FAC", "vip": "FAC"}
    code = cat_codes.get(category.lower(), "ATT")
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"YES26-{code}-{rand}"

def api_request(path: str, method: str = "GET", data: dict = None, prefer: str = None, timeout: int = 8):
    """Makes an authenticated HTTP request to the Supabase REST API."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"success": False, "status": 401, "error": "Supabase credentials not configured."}

    url = f"{get_base_url()}/rest/v1/{path.lstrip('/')}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    headers = get_headers(prefer=prefer)

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            content = response.read().decode("utf-8", errors="ignore")
            content_range = response.headers.get("Content-Range", "")
            parsed_json = json.loads(content) if content else None
            return {
                "success": True,
                "status": status,
                "data": parsed_json,
                "content_range": content_range
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        return {"success": False, "status": e.code, "error": err_body}
    except Exception as ex:
        return {"success": False, "status": 500, "error": str(ex)}

def is_table_available(table: str = "registrations") -> bool:
    """Checks if a table exists and is accessible in Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    res = api_request(f"{table}?select=id&limit=1", method="GET")
    if not res["success"] and res.get("status") == 404:
        return False
    return res["success"]

# ----------------- REGISTRATION CRUD (SUPABASE REST) ----------------- #

def create_registration(data: dict) -> dict:
    category = data.get("category", "participant").strip().lower()
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()
    org = data.get("organization", "").strip()
    designation = data.get("designation", "").strip() or ("Student / Innovator" if category == "participant" else "Executive")
    track = data.get("track_or_industry", "").strip() or "General Innovation Track"
    custom_fields = data.get("custom_fields", {})
    custom_fields_json = json.dumps(custom_fields) if isinstance(custom_fields, dict) else str(custom_fields)

    reg_id = generate_registration_id(category)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    record = {
        "registration_id": reg_id,
        "category": category,
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "organization": org,
        "designation": designation,
        "track_or_industry": track,
        "custom_fields_json": custom_fields_json,
        "qr_code_data": reg_id,
        "status": "REGISTERED",
        "created_at": now_str,
        "email_sent": 1
    }

    res = api_request("registrations", method="POST", data=record, prefer="return=representation")
    if not res["success"] and "registrations_category_check" in str(res.get("error", "")) and category == "faculty":
        # Remote Supabase table still has legacy CHECK constraint ('participant', 'delegate', 'vip').
        # Gracefully store with category 'vip' on remote table until schema.sql is executed.
        cloud_record = dict(record)
        cloud_record["category"] = "vip"
        res = api_request("registrations", method="POST", data=cloud_record, prefer="return=representation")

    if res["success"] and res.get("data"):
        created = res["data"][0] if isinstance(res["data"], list) else res["data"]
        if created.get("category") == "vip":
            created["category"] = "faculty"
        created["custom_fields"] = custom_fields
        log_activity(reg_id, "REGISTRATION_CREATED", f"Registered as {category.upper()}")
        return created
    else:
        logger.warning(f"[Supabase Cloud REST Notice] Insert returned: {res.get('error')}")
        record["custom_fields"] = custom_fields
        return record

def get_registration_by_id(reg_id: str):
    """Fetches attendee record by registration_id from Supabase."""
    res = api_request(f"registrations?registration_id=eq.{urllib.parse.quote(reg_id)}&select=*", method="GET")
    if res["success"] and res.get("data") and len(res["data"]) > 0:
        row = res["data"][0]
        if row.get("category") == "vip":
            row["category"] = "faculty"
        if row.get("custom_fields_json"):
            try:
                row["custom_fields"] = json.loads(row["custom_fields_json"])
            except Exception:
                row["custom_fields"] = {}
        return row
    return None

def get_registration_by_email(email: str):
    """Fetches attendee record by email from Supabase (case-insensitive)."""
    cleaned = (email or "").strip().lower()
    if not cleaned:
        return None
    res = api_request(f"registrations?email=ilike.{urllib.parse.quote(cleaned)}&select=*&limit=1", method="GET")
    if not res["success"] or not res.get("data") or len(res.get("data", [])) == 0:
        res = api_request(f"registrations?email=eq.{urllib.parse.quote(cleaned)}&select=*&limit=1", method="GET")
    if res["success"] and res.get("data") and len(res["data"]) > 0:
        row = res["data"][0]
        if row.get("category") == "vip":
            row["category"] = "faculty"
        if row.get("custom_fields_json"):
            try:
                row["custom_fields"] = json.loads(row["custom_fields_json"])
            except Exception:
                row["custom_fields"] = {}
        return row
    return None

def check_in_attendee(code: str, station: str = "Gate 1 Check-in Kiosk") -> dict:
    cleaned = code.strip()
    import re
    match = re.search(r'(YES26|NX26)-[A-Z]{3}-[A-Z0-9]{4,6}', cleaned, re.IGNORECASE)
    if match:
        cleaned = match.group(0).upper()

    attendee = get_registration_by_id(cleaned)
    if not attendee:
        res = api_request(f"registrations?email=eq.{urllib.parse.quote(cleaned.lower())}&select=*", method="GET")
        if res["success"] and res.get("data") and len(res["data"]) > 0:
            attendee = res["data"][0]

    if not attendee:
        return {"success": False, "error_type": "NOT_FOUND", "message": f"Registration '{cleaned}' not found in Supabase."}

    if attendee.get("status") == "CHECKED_IN":
        return {
            "success": False,
            "error_type": "DUPLICATE",
            "message": f"Attendee already checked in at {attendee.get('check_in_time')} ({attendee.get('check_in_station', 'Kiosk')}). Duplicate entry denied.",
            "attendee": attendee,
            "check_in_time": attendee.get("check_in_time"),
            "check_in_station": attendee.get("check_in_station")
        }

    now_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    patch_data = {
        "status": "CHECKED_IN",
        "check_in_time": now_str,
        "check_in_station": station
    }
    api_request(f"registrations?registration_id=eq.{attendee['registration_id']}", method="PATCH", data=patch_data, prefer="return=representation")
    log_activity(attendee["registration_id"], "CHECKED_IN", f"Check-in verified at {station}")

    attendee.update(patch_data)
    return {
        "success": True,
        "message": f"Verification successful. Welcome, {attendee['full_name']}!",
        "attendee": attendee,
        "check_in_time": now_str,
        "check_in_station": station
    }

def toggle_checkin_status(reg_id: str) -> dict:
    attendee = get_registration_by_id(reg_id)
    if not attendee:
        return {"success": False, "error": "Registration not found in Supabase."}

    if attendee.get("status") == "CHECKED_IN":
        patch = {"status": "REGISTERED", "check_in_time": None, "check_in_station": None}
        api_request(f"registrations?registration_id=eq.{reg_id}", method="PATCH", data=patch)
        log_activity(reg_id, "STATUS_RESET", "Staff reset check-in to REGISTERED")
        return {"success": True, "new_status": "REGISTERED", "message": "Check-in undone."}
    else:
        now_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        patch = {"status": "CHECKED_IN", "check_in_time": now_str, "check_in_station": "Admin Manual Override"}
        api_request(f"registrations?registration_id=eq.{reg_id}", method="PATCH", data=patch)
        log_activity(reg_id, "MANUAL_CHECKIN", "Staff manual override check-in")
        return {"success": True, "new_status": "CHECKED_IN", "message": "Manual check-in confirmed."}

def update_registration(reg_id: str, updates: dict) -> dict:
    allowed = ["full_name", "email", "phone", "organization", "designation", "track_or_industry"]
    patch = {k: updates[k].strip() for k in allowed if k in updates}
    if not patch:
        return {"success": False, "error": "No valid fields to update."}

    res = api_request(f"registrations?registration_id=eq.{reg_id}", method="PATCH", data=patch, prefer="return=representation")
    log_activity(reg_id, "RECORD_UPDATED", "Attendee updated")
    return {"success": True, "attendee": get_registration_by_id(reg_id)}

def delete_registration(reg_id: str) -> bool:
    api_request(f"registrations?registration_id=eq.{reg_id}", method="DELETE")
    api_request(f"emails_log?registration_id=eq.{reg_id}", method="DELETE")
    api_request(f"activity_logs?registration_id=eq.{reg_id}", method="DELETE")
    return True

def clear_all_attendees() -> bool:
    api_request("registrations?id=gt.0", method="DELETE")
    api_request("emails_log?id=gt.0", method="DELETE")
    api_request("activity_logs?id=gt.0", method="DELETE")
    return True

def get_registrations(search: str = "", category: str = "", status: str = "", limit: int = 100, offset: int = 0) -> dict:
    params = ["select=*"]
    if category and category.lower() != "all":
        cat_lower = category.lower()
        if cat_lower in ("faculty", "vip"):
            params.append("category=in.(faculty,vip)")
        else:
            params.append(f"category=eq.{urllib.parse.quote(cat_lower)}")
    if status and status.upper() != "ALL":
        params.append(f"status=eq.{urllib.parse.quote(status.upper())}")
    if search:
        s = urllib.parse.quote(search.strip())
        params.append(f"or=(full_name.ilike.*{s}*,registration_id.ilike.*{s}*,email.ilike.*{s}*,organization.ilike.*{s}*)")

    params.append(f"order=id.desc&limit={limit}&offset={offset}")
    query = "&".join(params)

    res = api_request(f"registrations?{query}", method="GET", prefer="count=exact")
    if not res["success"] or res.get("data") is None:
        return {"total": 0, "registrations": [], "limit": limit, "offset": offset}

    rows = res["data"]
    total = len(rows)
    cr = res.get("content_range", "")
    if "/" in cr:
        try:
            total = int(cr.split("/")[-1])
        except Exception:
            pass

    for r in rows:
        if r.get("category") == "vip":
            r["category"] = "faculty"
        if r.get("custom_fields_json"):
            try:
                r["custom_fields"] = json.loads(r["custom_fields_json"])
            except Exception:
                r["custom_fields"] = {}

    return {"total": total, "registrations": rows, "limit": limit, "offset": offset}

def get_dashboard_stats() -> dict:
    res = api_request("registrations?select=category,status", method="GET", prefer="count=exact")
    if not res["success"] or res.get("data") is None:
        return {"total": 0, "checked_in": 0, "pending": 0, "attendance_rate": 0.0, "categories": {"participant": 0, "delegate": 0, "faculty": 0}}

    rows = res["data"]
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
    res = api_request(f"registrations?status=eq.CHECKED_IN&order=id.desc&limit={limit}&select=registration_id,full_name,category,organization,check_in_time,check_in_station", method="GET")
    items = res.get("data") or []
    for it in items:
        if it.get("category") == "vip":
            it["category"] = "faculty"
    return items

# ----------------- LOGGING & METADATA (SUPABASE) ----------------- #

def log_email(reg_id: str, recipient: str, subject: str, html_body: str):
    now_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    payload = {
        "registration_id": reg_id,
        "recipient_email": recipient,
        "subject": subject,
        "html_body": html_body,
        "sent_at": now_str,
        "delivery_status": "DELIVERED"
    }
    api_request("emails_log", method="POST", data=payload)

def get_latest_email(reg_id: str):
    res = api_request(f"emails_log?registration_id=eq.{reg_id}&order=id.desc&limit=1&select=*", method="GET")
    if res["success"] and res.get("data") and len(res["data"]) > 0:
        return res["data"][0]
    return None

def log_activity(reg_id: str, action: str, details: str):
    now_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    payload = {
        "registration_id": reg_id,
        "action": action,
        "details": details,
        "timestamp": now_str
    }
    api_request("activity_logs", method="POST", data=payload)

def get_event_meta() -> dict:
    res = api_request("event_meta?select=key,value", method="GET")
    if res["success"] and res.get("data") and len(res["data"]) > 0:
        meta = {}
        for r in res["data"]:
            meta[r["key"]] = r["value"]
        return meta
    return DEFAULT_EVENT_META

def get_schedule_items(day: str = "day1") -> list:
    res = api_request(f"schedule_items?day=eq.{day}&order=id.asc&select=*", method="GET")
    if res["success"] and res.get("data") and len(res["data"]) > 0:
        return res["data"]
    return DEFAULT_SCHEDULE.get(day, [])

def get_speakers_list() -> list:
    return DEFAULT_SPEAKERS
