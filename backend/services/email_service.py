"""
YES 2026 Summit - Transactional Email & Digital Badge Service
VTU's Visvesvaraya Research and Innovation Foundation (VRIF), Belagavi
"""

import io
import base64
import logging
import qrcode
from datetime import datetime
from database import log_email
from backend.config import (
    SMTP_ENABLED, SMTP_SERVER, SMTP_PORT, SMTP_USE_TLS,
    SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_NAME, SMTP_FROM_EMAIL,
    get_smtp_config
)

logger = logging.getLogger("yes2026.email")

def generate_qr_base64(data_str: str) -> str:
    """
    Generates an ultra-scannable QR code optimized for camera optical sensors:
    - ISO/IEC 18004 compliant 4-module quiet zone (border=4)
    - 30% Reed-Solomon Error Correction (ERROR_CORRECT_H) for optical recovery
    - Pure high-contrast monochrome (pure black on pure white)
    - 12px per module for crisp resolution across all screens and cameras
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4
    )
    qr.add_data(data_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#000000", back_color="#ffffff")
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

def render_email_html(attendee: dict, qr_base64: str) -> str:
    """Generates an executive, responsive, 100% emoji-free HTML pass."""
    reg_id = attendee.get("registration_id", "YES26-ATT-00000")
    full_name = attendee.get("full_name", "Valued Attendee")
    category = attendee.get("category", "participant").upper()
    org = attendee.get("organization", "Partner Organization")
    designation = attendee.get("designation", "Delegate")
    track = attendee.get("track_or_industry", "Innovation & Deep-Tech")

    badge_theme = {
        "PARTICIPANT": {"bg": "#ea580c", "label": "INNOVATOR / PARTICIPANT PASS"},
        "DELEGATE":    {"bg": "#0284c7", "label": "DELEGATE & INDUSTRY ACCESS"},
        "FACULTY":     {"bg": "#7c3aed", "label": "FACULTY & ACADEMIC PASS"},
        "VIP":         {"bg": "#7c3aed", "label": "FACULTY & ACADEMIC PASS"}
    }.get(category, {"bg": "#7c3aed", "label": "OFFICIAL SUMMIT PASS"})

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ margin:0; padding:24px; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; background-color:#f1f5f9; color:#0f172a; }}
  .card {{ max-width:560px; margin:0 auto; background:#ffffff; border-radius:12px; border:1px solid #e2e8f0; box-shadow:0 10px 15px -3px rgba(0,0,0,0.05); overflow:hidden; }}
  .header {{ background:{badge_theme['bg']}; color:#ffffff; padding:28px 24px; text-align:center; }}
  .header h1 {{ margin:0; font-size:22px; letter-spacing:0.5px; font-weight:800; }}
  .header p {{ margin:6px 0 0; font-size:12px; opacity:0.95; font-weight:600; text-transform:uppercase; }}
  .content {{ padding:32px 28px; }}
  .badge-container {{ text-align:center; padding:20px; background:#f8fafc; border-radius:8px; border:1px solid #e2e8f0; margin:20px 0; }}
  .badge-container img {{ width:160px; height:160px; border-radius:4px; border:1px solid #cbd5e1; }}
  .reg-badge {{ display:inline-block; font-family:monospace; font-weight:700; font-size:16px; background:#ffffff; padding:6px 14px; border-radius:6px; border:1px solid #cbd5e1; margin-top:12px; color:#0f172a; }}
  .meta-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:13px; margin-top:20px; }}
  .meta-item {{ padding:10px; background:#f8fafc; border-radius:6px; border:1px solid #f1f5f9; }}
  .meta-label {{ font-size:11px; color:#64748b; font-weight:600; text-transform:uppercase; }}
  .meta-val {{ font-weight:700; color:#0f172a; margin-top:2px; }}
  .footer {{ background:#f8fafc; border-top:1px solid #e2e8f0; padding:20px; text-align:center; font-size:12px; color:#64748b; }}
</style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h1>YES 2026 SUMMIT ACCESS PASS</h1>
      <p>{badge_theme['label']}</p>
    </div>
    <div class="content">
      <h2 style="margin:0 0 8px; font-size:20px;">Welcome, {full_name}</h2>
      <p style="margin:0 0 16px; font-size:14px; color:#64748b; line-height:1.5;">
        Your official registration for <strong>Young Entrepreneurs Summit - YES 2026</strong> has been confirmed by VTU's Visvesvaraya Research & Innovation Foundation (VRIF), Belagavi.
      </p>

      <div class="badge-container">
        <img src="{qr_base64}" alt="Digital Access QR Code">
        <br>
        <span class="reg-badge">{reg_id}</span>
      </div>

      <div class="meta-grid">
        <div class="meta-item">
          <div class="meta-label">Organization</div>
          <div class="meta-val">{org}</div>
        </div>
        <div class="meta-item">
          <div class="meta-label">Designation</div>
          <div class="meta-val">{designation}</div>
        </div>
        <div class="meta-item">
          <div class="meta-label">Focus Track</div>
          <div class="meta-val">{track}</div>
        </div>
        <div class="meta-item">
          <div class="meta-label">Dates & Venue</div>
          <div class="meta-val">Sept 27-28 • VTU Belagavi</div>
        </div>
      </div>
    </div>
    <div class="footer">
      <p style="margin:0;">Organized by VTU's Visvesvaraya Research and Innovation Foundation (VRIF)</p>
      <p style="margin:4px 0 0;">Jnana Sangama, Machhe, Belagavi, Karnataka 590018</p>
    </div>
  </div>
</body>
</html>"""

def dispatch_smtp_email(recipient: str, subject: str, html_body: str, qr_png_bytes: bytes = None, pass_card_bytes: bytes = None, pdf_bytes: bytes = None, reg_id: str = "") -> dict:
    """Dispatches a real MIME email via Gmail/configured SMTP server."""
    cfg = get_smtp_config()
    if not cfg["enabled"] or not cfg["username"] or not cfg["password"]:
        logger.info(f"[Email Service] SMTP inactive. Email to {recipient} logged to outbox.")
        return {"sent": False, "reason": "SMTP_DISABLED"}

    # In testing mode, simulate dispatch without network latency or external timeouts
    try:
        from flask import current_app
        if current_app and current_app.config.get("TESTING"):
            logger.info(f"[Email Service] Test suite active: simulated email delivery to {recipient}")
            return {"sent": True, "method": "TEST_MOCK", "recipient": recipient}
    except Exception:
        pass

    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.image import MIMEImage
        from email.mime.application import MIMEApplication

        # Create the root multipart/mixed message
        msg_root = MIMEMultipart("mixed")
        msg_root["Subject"] = subject
        msg_root["From"] = f"{cfg['from_name']} <{cfg['from_email']}>"
        msg_root["To"] = recipient

        # Create alternative/related container for HTML and inline images
        msg_related = MIMEMultipart("related")
        msg_root.attach(msg_related)

        # Attach HTML body
        msg_html = MIMEText(html_body, "html", "utf-8")
        msg_related.attach(msg_html)

        # Attach Inline QR Code (CID)
        if qr_png_bytes:
            qr_img = MIMEImage(qr_png_bytes, _subtype="png")
            qr_img.add_header("Content-ID", "<qr_pass_code>")
            qr_img.add_header("Content-Disposition", "inline", filename=f"QR_{reg_id}.png")
            msg_related.attach(qr_img)

        # Attach dedicated QR Pass Card (PNG)
        if pass_card_bytes:
            pass_att = MIMEImage(pass_card_bytes, _subtype="png")
            pass_att.add_header("Content-Disposition", "attachment", filename=f"YES2026_QR_Pass_{reg_id}.png")
            msg_root.attach(pass_att)

        # Attach official PDF badge if available
        if pdf_bytes:
            pdf_att = MIMEApplication(pdf_bytes, _subtype="pdf")
            pdf_att.add_header("Content-Disposition", "attachment", filename=f"YES2026_Badge_{reg_id}.pdf")
            msg_root.attach(pdf_att)

        # Dispatch via SMTP with generous timeout for large attachments
        smtp_timeout = 45
        if cfg["use_tls"]:
            server = smtplib.SMTP(cfg["server"], cfg["port"], timeout=smtp_timeout)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP_SSL(cfg["server"], cfg["port"], timeout=smtp_timeout)
            server.ehlo()

        server.login(cfg["username"], cfg["password"])
        server.send_message(msg_root)
        server.quit()

        logger.info(f"[Email Service] Successfully delivered pass email to {recipient} via {cfg['server']}.")
        return {"sent": True, "method": "SMTP", "recipient": recipient}
    except Exception as err:
        logger.error(f"[Email Service] SMTP dispatch error for {recipient}: {err}", exc_info=True)
        return {"sent": False, "error": str(err)}

def send_confirmation_email(attendee: dict) -> dict:
    """Generates digital badge email, embeds QR code, and dispatches via SMTP."""
    reg_id = attendee.get("registration_id", "YES26-ATT-00000")
    recipient = attendee.get("email")
    subject = f"Official Access Pass & Badge • YES 2026 Summit [{reg_id}]"

    # 1. Generate QR Code bytes and base64
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4
    )
    qr.add_data(reg_id)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#000000", back_color="#ffffff")
    qr_buf = io.BytesIO()
    img.save(qr_buf, format="PNG")
    qr_png_bytes = qr_buf.getvalue()
    b64 = base64.b64encode(qr_png_bytes).decode("utf-8")
    qr_base64 = f"data:image/png;base64,{b64}"

    # 2. Render HTML body with inline CID image and data-uri fallback
    html_body = render_email_html(attendee, "cid:qr_pass_code")

    # 3. Generate QR Pass card and PDF badge bytes for attachments
    pass_card_bytes = None
    pdf_bytes = None
    try:
        from backend.services.pdf_service import generate_qr_pass_card, generate_attendee_pdf
        pass_card_bytes = generate_qr_pass_card(attendee)
        pdf_bytes = generate_attendee_pdf(attendee)
    except Exception as ex:
        logger.warning(f"[Email Service] Notice generating attachments: {ex}")

    # 4. Dispatch real email via SMTP
    dispatch_res = dispatch_smtp_email(
        recipient=recipient,
        subject=subject,
        html_body=html_body,
        qr_png_bytes=qr_png_bytes,
        pass_card_bytes=pass_card_bytes,
        pdf_bytes=pdf_bytes,
        reg_id=reg_id
    )

    # 5. Log to audit outbox table in Supabase
    delivery_status = "DELIVERED" if dispatch_res.get("sent") else "QUEUED"
    try:
        log_email(reg_id, recipient, subject, html_body)
    except Exception as e:
        logger.warning(f"[Email Service] Notice logging email: {e}")

    return {
        "status": delivery_status,
        "recipient": recipient,
        "subject": subject,
        "qr_base64": qr_base64,
        "sent_at": datetime.now().isoformat(),
        "smtp": dispatch_res
    }

