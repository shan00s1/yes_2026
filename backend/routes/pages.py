"""
YES 2026 Summit - Page View Routes
"""

import socket
from flask import Blueprint, render_template, request, session, redirect
from backend.config import ADMIN_USERNAME, ADMIN_PASSWORD
from database import get_event_meta, get_schedule_items, get_speakers_list

pages_bp = Blueprint("pages", __name__)

def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@pages_bp.route("/")
def index():
    meta = get_event_meta()
    day1 = get_schedule_items("day1")
    day2 = get_schedule_items("day2")
    speakers = get_speakers_list()
    return render_template("index.html", event=meta, day1=day1, day2=day2, speakers=speakers)

@pages_bp.route("/register")
def register_page():
    category = request.args.get("category", "participant")
    return render_template("register.html", initial_category=category)

@pages_bp.route("/checkin")
def checkin_page():
    if not session.get("admin_logged_in"):
        return redirect("/admin")
    lan_ip = get_lan_ip()
    return render_template("checkin.html", lan_ip=lan_ip, is_https=request.is_secure)

@pages_bp.route("/admin", methods=["GET", "POST"])
def admin_page():
    if request.method == "POST":
        user = request.form.get("username", "").strip()
        pwd = request.form.get("password", "").strip()
        if user == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect("/admin")
        else:
            return render_template("admin_login.html", error="Invalid admin username or password.")
            
    if not session.get("admin_logged_in"):
        return render_template("admin_login.html")
        
    lan_ip = get_lan_ip()
    return render_template("admin.html", lan_ip=lan_ip, is_https=request.is_secure)

@pages_bp.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect("/admin")
