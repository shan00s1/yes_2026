"""
YES 2026 Summit - Official PDF Pass & ID Badge Generator
VTU's Visvesvaraya Research and Innovation Foundation (VRIF), Belagavi
"""

import io
import os
import hashlib
from pathlib import Path

# Safe hashlib wrapper to prevent OpenSSL 'usedforsecurity' TypeError on Python 3.8 Windows
_orig_md5 = hashlib.md5
def _safe_md5(*args, **kwargs):
    kwargs.pop('usedforsecurity', None)
    return _orig_md5(*args, **kwargs)
hashlib.md5 = _safe_md5

import qrcode
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent.parent
IMG_DIR = BASE_DIR / "frontend" / "static" / "img"

CATEGORY_CONFIG = {
    "faculty": {
        "title": "FACULTY & RESEARCH PASS",
        "primary_color": (124/255, 58/255, 237/255),    # Royal Violet
        "bg_color": (245/255, 243/255, 255/255),
        "badge_tag": "ACADEMIC CONCLAVE • R&D SESSIONS"
    },
    "vip": {
        "title": "FACULTY & RESEARCH PASS",
        "primary_color": (124/255, 58/255, 237/255),    # Royal Violet
        "bg_color": (245/255, 243/255, 255/255),
        "badge_tag": "ACADEMIC CONCLAVE • R&D SESSIONS"
    },
    "delegate": {
        "title": "CORPORATE DELEGATE",
        "primary_color": (2/255, 132/255, 199/255),    # Cyan/Blue
        "bg_color": (224/255, 242/255, 254/255),
        "badge_tag": "B2B SUITES • NETWORKING DINNER"
    },
    "participant": {
        "title": "PARTICIPANT / INNOVATOR",
        "primary_color": (234/255, 88/255, 12/255),   # Orange/Coral
        "bg_color": (255/255, 237/255, 213/255),
        "badge_tag": "TOP 20 SHOWCASE • TBI SESSIONS"
    }
}

def generate_attendee_pdf(attendee):
    """
    Generates a high-resolution, print-ready official PDF pass for an attendee.
    Returns bytes of the PDF.
    """
    try:
        return _generate_reportlab_pdf(attendee)
    except Exception as e:
        # Fallback to Pillow PDF generator if ReportLab encounters any environment issue
        return _generate_pillow_pdf(attendee)

def _generate_reportlab_pdf(attendee):
    from reportlab.lib.pagesizes import A5
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors

    buf = io.BytesIO()
    # A5 size: 419.5 x 595.3 points
    width, height = A5
    c = canvas.Canvas(buf, pagesize=A5)
    c.setTitle(f"YES 2026 Summit Pass - {attendee.get('registration_id', 'Pass')}")

    cat_key = (attendee.get("category") or "participant").lower()
    cat_info = CATEGORY_CONFIG.get(cat_key, CATEGORY_CONFIG["participant"])
    prim_col = colors.Color(*cat_info["primary_color"])
    bg_col = colors.Color(*cat_info["bg_color"])

    # Outer decorative border
    c.setStrokeColor(prim_col)
    c.setLineWidth(2)
    c.roundRect(16, 16, width - 32, height - 32, 12, stroke=1, fill=0)

    # Top Header Background
    c.setFillColor(colors.HexColor("#0f172a")) # Dark Slate
    c.roundRect(20, height - 100, width - 40, 76, 8, stroke=0, fill=1)

    # Embed Logos in Header
    vrif_logo_path = IMG_DIR / "VRIF LOGO.png"
    yes_mascot_path = IMG_DIR / "Young Entrepreneur SuMmit (9).png"

    if vrif_logo_path.exists():
        try:
            c.drawImage(str(vrif_logo_path), 32, height - 92, width=95, height=60, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    if yes_mascot_path.exists():
        try:
            c.drawImage(str(yes_mascot_path), width - 78, height - 90, width=44, height=56, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    # Header Titles
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 52, "YES 2026")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#94a3b8"))
    c.drawCentredString(width / 2, height - 68, "YOUNG ENTREPRENEURS SUMMIT")
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.HexColor("#38bdf8"))
    c.drawCentredString(width / 2, height - 82, "VTU VRIF BELAGAVI")

    # Category Ribbon Banner
    c.setFillColor(prim_col)
    c.rect(20, height - 132, width - 40, 26, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, height - 124, cat_info["title"])

    # Registration Code Pill
    reg_id = attendee.get("registration_id", "YES26-PAR-XXXX")
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.setStrokeColor(colors.HexColor("#e2e8f0"))
    c.setLineWidth(1)
    c.roundRect(width/2 - 90, height - 170, 180, 28, 6, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#0284c7"))
    c.setFont("Courier-Bold", 14)
    c.drawCentredString(width / 2, height - 162, reg_id)

    # Attendee Details
    full_name = (attendee.get("full_name") or "Attendee Name").strip()
    organization = (attendee.get("organization") or "Organization").strip()
    designation = (attendee.get("designation") or "Innovator").strip()
    email = (attendee.get("email") or "").strip()

    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 202, full_name)

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawCentredString(width / 2, height - 218, designation)

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawCentredString(width / 2, height - 232, organization)

    if email:
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.drawCentredString(width / 2, height - 246, email)

    # Divider line
    c.setStrokeColor(colors.HexColor("#e2e8f0"))
    c.line(40, height - 258, width - 40, height - 258)

    # High-Res Scannable QR Code (ISO/IEC 18004 compliant 4-module quiet zone & 30% error correction)
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4
    )
    qr.add_data(reg_id)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_buf.seek(0)

    from reportlab.lib.utils import ImageReader
    qr_reader = ImageReader(qr_buf)
    qr_size = 150
    qr_x = (width - qr_size) / 2
    qr_y = height - 425

    # White box with clean contrast for optical camera scan
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#94a3b8"))
    c.setLineWidth(1)
    c.roundRect(qr_x - 10, qr_y - 10, qr_size + 20, qr_size + 20, 8, stroke=1, fill=1)
    c.drawImage(qr_reader, qr_x, qr_y, width=qr_size, height=qr_size)

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawCentredString(width / 2, qr_y - 18, "OFFICIAL CHECK-IN QR CREDENTIAL")

    # Venue & Date Info Box
    c.setFillColor(colors.HexColor("#f1f5f9"))
    c.roundRect(24, 76, width - 48, 52, 6, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width / 2, 112, "27th & 28th September 2026 • 10.00 AM Onwards")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawCentredString(width / 2, 98, "Second Floor, VRIF Building, TBI Centre, VTU Belagavi")
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(prim_col)
    c.drawCentredString(width / 2, 84, cat_info["badge_tag"])

    # Bottom Endorsement Bar
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#94a3b8"))
    c.drawCentredString(width / 2, 42, "Supported by Govt. of Karnataka (Dept. of E, IT & Bt) • K-tech • Startup Karnataka • Early Founders")
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(width / 2, 28, "Please present this pass at the venue entrance scanner kiosk for lanyard badge issuance.")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()

def _generate_pillow_pdf(attendee):
    """
    Bulletproof Pillow-based PDF fallback generator.
    """
    from PIL import ImageDraw, ImageFont

    w, h = 1200, 1750
    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header bar
    draw.rectangle([(0, 0), (w, 240)], fill=(15, 23, 42))

    cat_key = (attendee.get("category") or "participant").lower()
    cat_colors = {
        "faculty": (124, 58, 237),
        "vip": (124, 58, 237),
        "delegate": (2, 132, 199),
        "participant": (234, 88, 12)
    }
    banner_col = cat_colors.get(cat_key, (234, 88, 12))

    # Category Ribbon
    draw.rectangle([(0, 240), (w, 320)], fill=banner_col)

    # Load and paste logos if available
    vrif_logo = IMG_DIR / "VRIF LOGO.png"
    if vrif_logo.exists():
        try:
            v_img = Image.open(vrif_logo).convert("RGBA")
            v_img.thumbnail((260, 160))
            img.paste(v_img, (40, 40), mask=v_img)
        except Exception:
            pass

    # Generate QR Code (ISO/IEC 18004 compliant 4-module quiet zone & 30% error correction)
    reg_id = attendee.get("registration_id", "YES26-PAR-0001")
    qr = qrcode.QRCode(
        box_size=12,
        border=4,
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    qr.add_data(reg_id)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize((450, 450))

    img.paste(qr_img, ((w - 450) // 2, 700))

    # Text rendering (simple default bitmap or basic)
    # Registration ID Box
    draw.rectangle([(w//2 - 280, 400), (w//2 + 280, 480)], outline=banner_col, width=3, fill=(248, 250, 252))

    # Save to PDF buffer
    buf = io.BytesIO()
    img.save(buf, format="PDF", resolution=150.0)
    buf.seek(0)
    return buf.getvalue()

def generate_qr_pass_card(attendee: dict) -> bytes:
    """
    Generates a dedicated high-resolution, camera-optimized QR Pass Card (PNG).
    Contains:
    - Summit Header & Category Banner
    - Giant 480x480 High-Contrast Pure Monochrome QR Code
    - Large, Bold, Clear Registration ID
    - Attendee Name & Institution
    """
    from PIL import Image, ImageDraw, ImageFont

    w, h = 700, 880
    card = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(card)

    cat_key = (attendee.get("category") or "participant").lower()
    cat_colors = {
        "faculty": (124, 58, 237),
        "vip": (124, 58, 237),
        "delegate": (2, 132, 199),
        "participant": (234, 88, 12)
    }
    cat_titles = {
        "faculty": "FACULTY & RESEARCH PASS",
        "vip": "FACULTY & RESEARCH PASS",
        "delegate": "OFFICIAL DELEGATE PASS",
        "participant": "PARTICIPANT / INNOVATOR PASS"
    }
    accent_color = cat_colors.get(cat_key, (2, 132, 199))
    cat_title = cat_titles.get(cat_key, "OFFICIAL SUMMIT PASS")

    # Outer border
    draw.rectangle([(8, 8), (w - 8, h - 8)], outline=accent_color, width=4)
    # Header background
    draw.rectangle([(8, 8), (w - 8, 90)], fill=(15, 23, 42))

    # Font handling with safe fallbacks
    font_title = font_id = font_name = font_sub = ImageFont.load_default()
    for fpath in ["arial.ttf", "calibri.ttf", "segoeui.ttf", "DejaVuSans.ttf"]:
        try:
            font_title = ImageFont.truetype(fpath, 23)
            font_name = ImageFont.truetype(fpath, 25)
            font_sub = ImageFont.truetype(fpath, 15)
            break
        except Exception:
            pass

    for fpath in ["cour.ttf", "consolas.ttf", "courbd.ttf", "DejaVuSansMono.ttf"]:
        try:
            font_id = ImageFont.truetype(fpath, 34)
            break
        except Exception:
            pass

    # Header text
    draw.text((w // 2, 34), "YES 2026 • OFFICIAL CHECK-IN PASS", fill=(255, 255, 255), anchor="mm", font=font_title)
    draw.text((w // 2, 68), "VTU VRIF BELAGAVI • VENUE ACCESS CREDENTIAL", fill=(56, 189, 248), anchor="mm", font=font_sub)

    # Big Scannable QR Code (480x480)
    reg_id = attendee.get("registration_id", "YES26-ATT-00000")
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=14,
        border=4
    )
    qr.add_data(reg_id)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize((480, 480), Image.Resampling.NEAREST)
    card.paste(qr_img, ((w - 480) // 2, 115))

    # Registration ID Box
    box_w = 460
    box_h = 66
    box_x = (w - box_w) // 2
    box_y = 618
    draw.rounded_rectangle([(box_x, box_y), (box_x + box_w, box_y + box_h)], radius=12, fill=(241, 245, 249), outline=(203, 213, 225), width=2)
    draw.text((w // 2, box_y + box_h // 2), reg_id, fill=accent_color, anchor="mm", font=font_id)

    # Attendee Details
    full_name = attendee.get("full_name", "Valued Attendee")
    org = attendee.get("organization", "Institution")
    draw.text((w // 2, 715), full_name, fill=(15, 23, 42), anchor="mm", font=font_name)
    draw.text((w // 2, 748), f"{org} • {cat_title}", fill=(71, 85, 105), anchor="mm", font=font_sub)
    draw.text((w // 2, 830), "Scan this QR code directly at the venue kiosk camera", fill=(148, 163, 184), anchor="mm", font=font_sub)

    buf = io.BytesIO()
    card.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()
