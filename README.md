# YES 2026 - Young Entrepreneurs Summit

> **Official Event Portal & Access Management System**  
> Organized by **Visvesvaraya Technological University (VTU)**  
> **Visvesvaraya Research and Innovation Foundation (VRIF)**, Belagavi, Karnataka  
> In association with **K-tech**, **IT & BT Govt of Karnataka**, and **Startup Karnataka**

---

## 🌟 Overview

**YES 2026** is the flagship annual entrepreneurship and innovation summit of VTU VRIF. This repository contains the complete production web application, attendee registration system, QR camera check-in kiosk, and administrative console.

### Key Features
- **Official Summit Landing Page**: High-impact poster-aligned typography, event agenda, ecosystem partners, and VTU leadership showcase.
- **Pass Registration System**:
  - 100% Free Complimentary Pass Pathways: **Participant / Innovator**, **Corporate Delegate**, and **Faculty & Academic Mentors**.
  - Interactive live badge preview generator.
  - **Duplicate Email Prevention**: Prevents duplicate registrations per attendee email.
- **Automated Confirmation Delivery**: Dispatches email passes with digital QR code and badge attachments via SMTP.
- **Camera QR Scanner & Check-in Desk (`/checkin`)**:
  - High-speed browser camera scanner using ZXing & jsQR.
  - Real-time duplicate entry prevention with audit logs.
  - **Lanyard ID Badge Printing**: Formatted for standard 3.5" × 5.2" lanyard cards and vector PDF downloads.
- **Centralized Admin Dashboard (`/admin`)**:
  - Real-time attendance KPIs and category breakdown charts.
  - Attendee search, filter, inline edit modal, check-in toggle, and CSV export.
- **Database Engine**:
  - Powered by **Supabase PostgreSQL** cloud database with local fallback caching.

---

## 🚀 Quick Start (Local Run)

### 1. Prerequisites
- Python 3.8+ installed
- Git

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/shan00s1/yes_2026.git
cd yes_2026

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

Configure your `.env`:
```ini
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=your-anon-key
SUPABASE_SECRET_KEY=your-service-role-key

ADMIN_USERNAME=admin
ADMIN_PASSWORD=yes2026
SECRET_KEY=your-secret-key

MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### 4. Run the Server
```bash
python app.py
```
Open your browser at:
- **Public Landing Page**: `http://localhost:5000/`
- **Pass Registration**: `http://localhost:5000/register`
- **Scanner Kiosk**: `http://localhost:5000/checkin`
- **Admin Console**: `http://localhost:5000/admin` (Default: `admin` / `yes2026`)

---

## 🌐 Free Cloud Hosting Options

This application can be deployed for free on multiple cloud platforms:

| Platform | Tier | Best For | Deploy Guide |
|---|---|---|---|
| **Render** | Free Web Service | Full Flask Server with WebSocket/Camera | Connect GitHub repo, set build: `pip install -r requirements.txt`, start: `python app.py` |
| **Railway** | Free Trial / Hobby | Instant full-stack deployment | Connect GitHub repo, add env variables, auto-deploys |
| **Vercel** | Free Hobby | Serverless WSGI via `vercel.json` | Run `vercel` CLI or connect repository |
| **PythonAnywhere** | Free Tier | Web app hosting | Upload repo or clone via bash console |

---

## 🧪 Testing

Run the comprehensive unit test suite:
```bash
python -m unittest test_system.py
```
Validates all endpoints, category registration, duplicate check-in rules, duplicate email prevention, admin authentication, and PDF pass generation.

---

## 📜 License
Developed for Visvesvaraya Research and Innovation Foundation (VRIF), VTU Belagavi.
