"""
YES 2026 Summit - Attendee Registration & Check-in APIs
"""

import io
import json
import logging
import qrcode
from flask import Blueprint, request, jsonify, send_file
from database import (
    create_registration, check_in_attendee, get_recent_checkins,
    get_dashboard_stats, get_latest_email, get_registration_by_id,
    get_registration_by_email
)
from backend.services.email_service import send_confirmation_email, generate_qr_base64

logger = logging.getLogger("yes2026.api.attendees")
attendees_bp = Blueprint("attendees_api", __name__)

@attendees_bp.route("/api/register", methods=["POST"])
def api_register():
    try:
        data = request.get_json(force=True) if request.is_json else request.form.to_dict()
        
        category = data.get("category", "participant").strip().lower()
        if category == "vip":
            category = "faculty"
        if category not in ["participant", "delegate", "faculty"]:
            return jsonify({"success": False, "error": "Invalid category"}), 400
            
        full_name = data.get("full_name", "").strip()
        email = data.get("email", "").strip().lower()
        phone = data.get("phone", "").strip()
        org = data.get("organization", "").strip()
        
        if not full_name or not email or not phone or not org:
            return jsonify({"success": False, "error": "Please fill in all required fields (Name, Email, Phone, Organization)."}), 400

        # Duplicate email prevention check
        existing = get_registration_by_email(email)
        if existing:
            reg_id = existing.get("registration_id", "YES26-PASS")
            return jsonify({
                "success": False,
                "error": f"The email '{email}' is already registered for YES 2026 (Pass ID: {reg_id}). Each email address can only register once. Please check your inbox for your digital pass or contact the Secretariat.",
                "error_type": "DUPLICATE_EMAIL",
                "registration_id": reg_id
            }), 400
            
        custom_fields = data.get("custom_fields", {})
        if isinstance(custom_fields, str):
            try:
                custom_fields = json.loads(custom_fields)
            except Exception:
                custom_fields = {}
                
        if category == "participant":
            for f in ["tshirt_size", "portfolio_url", "interests", "experience_level"]:
                if f in data: custom_fields[f] = data[f]
        elif category == "delegate":
            for f in ["b2b_networking", "tax_id"]:
                if f in data: custom_fields[f] = data[f]
        elif category in ["faculty", "vip"]:
            for f in [
                "title", "honorific", "faculty_title", "academic_role", "faculty_role",
                "department", "faculty_dept", "college_code", "faculty_college_code",
                "engagement_role", "faculty_engagement", "specialization", "faculty_specialization",
                "protocol_needs", "seating_pref", "emergency_contact"
            ]:
                if f in data: custom_fields[f] = data[f]

        record_data = {
            "category": category,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "organization": org,
            "designation": data.get("designation", ""),
            "track_or_industry": data.get("track_or_industry", "General"),
            "custom_fields": custom_fields
        }
        
        attendee = create_registration(record_data)
        email_result = send_confirmation_email(attendee)
        
        return jsonify({
            "success": True,
            "message": f"Registration successful! Confirmation pass sent to {email}.",
            "attendee": attendee,
            "registration_id": attendee["registration_id"],
            "qr_code_base64": email_result["qr_base64"]
        })
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@attendees_bp.route("/api/checkin/scan", methods=["POST"])
def api_checkin_scan():
    try:
        data = request.get_json(force=True)
        raw_code = data.get("code", "").strip()
        station = data.get("station", "Main Kiosk")
        
        if not raw_code:
            return jsonify({"success": False, "error_type": "EMPTY", "message": "No QR code or registration ID provided."}), 400

        # Robust code extraction (handles raw ID, URLs, or query parameters)
        code = raw_code
        import re
        match = re.search(r"YES26-[A-Z]{3}-[A-Z0-9]{4,8}", raw_code, re.IGNORECASE)
        if match:
            code = match.group(0).upper()
            
        result = check_in_attendee(code, station)
        if "attendee" in result and result["attendee"]:
            result["attendee"]["qr_base64"] = generate_qr_base64(result["attendee"]["registration_id"])
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Check-in scan error: {e}", exc_info=True)
        return jsonify({"success": False, "error_type": "SERVER_ERROR", "message": str(e)}), 500

@attendees_bp.route("/api/checkin/recent")
def api_recent_checkins():
    recent = get_recent_checkins(10)
    stats = get_dashboard_stats()
    return jsonify({
        "success": True,
        "recent_checkins": recent,
        "total_checked_in": stats["checked_in"],
        "total_registered": stats["total"]
    })

@attendees_bp.route("/api/emails/latest/<reg_id>")
def api_view_latest_email(reg_id):
    email_record = get_latest_email(reg_id)
    if not email_record:
        return "<h3>No logged confirmation email found for this registration.</h3>", 404
    return email_record["html_body"]

@attendees_bp.route("/api/registration/<reg_id>/qr.png")
def api_get_qr_png(reg_id):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4
    )
    qr.add_data(reg_id)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#000000", back_color="#ffffff")
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

@attendees_bp.route("/api/registration/<reg_id>")
def api_get_registration_details(reg_id):
    try:
        attendee = get_registration_by_id(reg_id)
        if not attendee:
            return jsonify({"success": False, "error": "Registration ID not found"}), 404
        attendee["qr_base64"] = generate_qr_base64(reg_id)
        return jsonify({"success": True, "attendee": attendee})
    except Exception as e:
        logger.error(f"Error fetching registration {reg_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@attendees_bp.route("/api/registration/<reg_id>/pdf")
def api_download_registration_pdf(reg_id):
    try:
        attendee = get_registration_by_id(reg_id)
        if not attendee:
            return jsonify({"success": False, "error": "Registration ID not found"}), 404
        
        from backend.services.pdf_service import generate_attendee_pdf
        pdf_bytes = generate_attendee_pdf(attendee)
        
        buf = io.BytesIO(pdf_bytes)
        buf.seek(0)
        as_att = request.args.get("download") == "1"
        return send_file(
            buf,
            mimetype="application/pdf",
            as_attachment=as_att,
            download_name=f"YES2026_Badge_{reg_id}.pdf"
        )
    except Exception as e:
        logger.error(f"Error generating PDF for {reg_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"PDF Generation Error: {str(e)}"}), 500

@attendees_bp.route("/api/registration/<reg_id>/qr-pass.png")
def api_download_qr_pass(reg_id):
    try:
        attendee = get_registration_by_id(reg_id)
        if not attendee:
            return jsonify({"success": False, "error": "Registration ID not found"}), 404

        from backend.services.pdf_service import generate_qr_pass_card
        card_bytes = generate_qr_pass_card(attendee)

        buf = io.BytesIO(card_bytes)
        buf.seek(0)
        return send_file(
            buf,
            mimetype="image/png",
            as_attachment=True,
            download_name=f"YES2026_QR_Pass_{reg_id}.png"
        )
    except Exception as e:
        logger.error(f"Error generating QR pass card for {reg_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"QR Pass Generation Error: {str(e)}"}), 500
