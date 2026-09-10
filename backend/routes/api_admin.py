"""
YES 2026 Summit - Admin Console & Management APIs
"""

import io
import csv
from flask import Blueprint, request, jsonify, Response
from database import (
    get_dashboard_stats, get_registrations, get_registration_by_id,
    update_registration, delete_registration, toggle_checkin_status,
    clear_all_attendees
)
from backend.services.email_service import send_confirmation_email, generate_qr_base64

admin_api_bp = Blueprint("admin_api", __name__)

@admin_api_bp.route("/api/admin/stats")
def api_admin_stats():
    stats = get_dashboard_stats()
    return jsonify({"success": True, "stats": stats})

@admin_api_bp.route("/api/admin/registrations")
def api_admin_registrations():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip()
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    
    data = get_registrations(search, category, status, limit, offset)
    return jsonify({"success": True, "data": data})

@admin_api_bp.route("/api/admin/registration/<reg_id>", methods=["GET", "PUT", "DELETE"])
def api_admin_single_reg(reg_id):
    if request.method == "GET":
        reg = get_registration_by_id(reg_id)
        if not reg:
            return jsonify({"success": False, "error": "Not found"}), 404
        reg["qr_base64"] = generate_qr_base64(reg["registration_id"])
        return jsonify({"success": True, "attendee": reg})
        
    elif request.method == "PUT":
        data = request.get_json(force=True)
        updated = update_registration(reg_id, data)
        return jsonify({"success": True, "attendee": updated})
        
    elif request.method == "DELETE":
        delete_registration(reg_id)
        return jsonify({"success": True, "message": f"Registration {reg_id} deleted."})

@admin_api_bp.route("/api/admin/registration/<reg_id>/toggle-checkin", methods=["POST"])
def api_admin_toggle_checkin(reg_id):
    updated = toggle_checkin_status(reg_id)
    if not updated:
        return jsonify({"success": False, "error": "Not found"}), 404
    return jsonify({"success": True, "attendee": updated})

@admin_api_bp.route("/api/admin/registration/<reg_id>/resend-email", methods=["POST"])
def api_admin_resend_email(reg_id):
    reg = get_registration_by_id(reg_id)
    if not reg:
        return jsonify({"success": False, "error": "Not found"}), 404
    email_res = send_confirmation_email(reg)
    return jsonify({"success": True, "message": f"Confirmation email resent to {reg['email']}.", "email": email_res})

@admin_api_bp.route("/api/admin/broadcast-emails", methods=["POST"])
def api_admin_broadcast_emails():
    """Broadcasts official digital pass & badge emails to all registered attendees."""
    res = get_registrations(limit=5000, offset=0)
    attendees = res.get("registrations", [])
    
    sent_count = 0
    failed_count = 0
    results = []

    for att in attendees:
        email = (att.get("email") or "").strip()
        if not email or "@" not in email:
            failed_count += 1
            continue
        try:
            r = send_confirmation_email(att)
            if r.get("smtp", {}).get("sent") or r.get("status") in ("DELIVERED", "SENT"):
                sent_count += 1
            else:
                failed_count += 1
            results.append({"reg_id": att.get("registration_id"), "email": email, "sent": True})
        except Exception as e:
            failed_count += 1
            results.append({"reg_id": att.get("registration_id"), "email": email, "sent": False, "error": str(e)})

    return jsonify({
        "success": True,
        "total": len(attendees),
        "sent": sent_count,
        "failed": failed_count,
        "message": f"Dispatched official pass emails to {sent_count} of {len(attendees)} attendees."
    })

@admin_api_bp.route("/api/admin/clear-all", methods=["POST"])
def api_admin_clear_all():
    """Wipes all registration and check-in records for a completely clean slate."""
    clear_all_attendees()
    return jsonify({"success": True, "message": "All registration records cleared. Database is 100% clean."})

@admin_api_bp.route("/api/admin/export/csv")
def api_export_csv():
    res = get_registrations(limit=50000, offset=0)
    registrations = res["registrations"]
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Registration ID", "Category", "Full Name", "Email", "Phone",
        "Organization", "Designation", "Track / Industry", "Status",
        "Check-in Time", "Check-in Station", "Registered At", "Custom Fields Details"
    ])
    
    for r in registrations:
        custom_str = "; ".join([f"{k}: {v}" for k, v in r.get("custom_fields", {}).items()])
        writer.writerow([
            r.get("registration_id", ""),
            r.get("category", "").upper(),
            r.get("full_name", ""),
            r.get("email", ""),
            r.get("phone", ""),
            r.get("organization", ""),
            r.get("designation", ""),
            r.get("track_or_industry", ""),
            r.get("status", ""),
            r.get("check_in_time", "") or "N/A",
            r.get("check_in_station", "") or "N/A",
            r.get("created_at", ""),
            custom_str
        ])
        
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=yes2026_registrations.csv"}
    )
