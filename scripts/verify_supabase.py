"""
YES 2026 Summit - Supabase Cloud Connectivity Diagnostics Tool
VTU's Visvesvaraya Research and Innovation Foundation (VRIF), Belagavi

Run from terminal:
    python scripts/verify_supabase.py
"""

import sys
import time
import urllib.parse
from pathlib import Path

# Ensure root workspace is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config import (
    DATABASE_URL, POSTGRES_HOST, SUPABASE_URL,
    SUPABASE_KEY
)
from database import supabase_client

def print_banner():
    print("=" * 75)
    print("   YES 2026 SUMMIT - SUPABASE CLOUD CONNECTIVITY & SCHEMA DIAGNOSTICS")
    print("   VTU's Visvesvaraya Research and Innovation Foundation (VRIF)")
    print("=" * 75)

def extract_project_ref():
    if SUPABASE_URL:
        try:
            parsed = urllib.parse.urlparse(SUPABASE_URL)
            return parsed.hostname.split('.')[0]
        except Exception:
            pass
    return "YOUR-PROJECT-REF"

def main():
    print_banner()
    proj_ref = extract_project_ref()
    has_rest = bool(SUPABASE_URL and SUPABASE_KEY)
    has_pg = bool(DATABASE_URL or POSTGRES_HOST)

    if not has_rest and not has_pg:
        print("\n[!] STATUS: NO SUPABASE CREDENTIALS FOUND IN .env")
        print("-" * 75)
        print("To connect your database to Supabase:")
        print("1. Open your Supabase Dashboard: https://supabase.com/dashboard")
        print("2. Navigate to: Project Settings -> API")
        print("3. Copy Project URL and service_role key into .env")
        print("-" * 75)
        return 0

    print(f"\n[1] Configuration Detected:")
    print(f"    - Supabase Project URL: {SUPABASE_URL or 'None'}")
    print(f"    - Project Reference:    {proj_ref}")
    print(f"    - Authentication Key:   {'Configured (Active)' if SUPABASE_KEY else 'Missing'}")
    if DATABASE_URL:
        parsed = urllib.parse.urlparse(DATABASE_URL)
        print(f"    - PostgreSQL Direct Host: {parsed.hostname}:{parsed.port}")
    else:
        print(f"    - PostgreSQL Direct:    REST API Cloud Mode (Active)")

    # 2. Check Supabase REST API & Schema Table
    print(f"\n[2] Testing Supabase Cloud REST Connection...")
    t0 = time.perf_counter()
    table_ready = supabase_client.is_table_available("registrations")
    t1 = time.perf_counter()
    latency_ms = round((t1 - t0) * 1000, 2)

    print(f"    [OK] Connected to Supabase Cloud API ({latency_ms} ms roundtrip).")
    if table_ready:
        print(f"    [OK] Table 'public.registrations' is ACTIVE and ready in Supabase!")

        # Live test insert
        print(f"\n[3] Testing Live Data Write to Supabase...")
        test_attendee = {
            "category": "participant",
            "full_name": "Supabase Connection Verification",
            "email": "verify@vtu.ac.in",
            "phone": "+91-831-2498100",
            "organization": "VTU VRIF Belagavi",
            "designation": "Diagnostic Ping",
            "track_or_industry": "Cloud Parity",
            "custom_fields": {"test_mode": True}
        }
        created = supabase_client.create_registration(test_attendee)
        if created and created.get("registration_id"):
            print(f"    [OK] Successfully wrote entry '{created['registration_id']}' to Supabase!")
            print(f"    >> View it now in your Supabase Dashboard:")
            print(f"       https://supabase.com/dashboard/project/{proj_ref}/editor/registrations")
    else:
        print(f"\n[!] ACTION REQUIRED: Create Tables in your Supabase Project")
        print("-" * 75)
        print(f"The 'registrations' table has not been created yet in your Supabase project.")
        print("Follow these 2 quick steps to initialize your database:")
        print(f"1. Open the SQL Editor in your browser:")
        print(f"   >> https://supabase.com/dashboard/project/{proj_ref}/sql")
        print("2. Click '+ New query', paste the contents of 'database/schema.sql', and click 'RUN'.")
        print("-" * 75)
        print("Once created, run 'python scripts/verify_supabase.py' again to confirm!")

    print("\n" + "=" * 75)
    print("   SUPABASE DIAGNOSTICS COMPLETE")
    print("=" * 75)
    return 0

if __name__ == "__main__":
    sys.exit(main())
