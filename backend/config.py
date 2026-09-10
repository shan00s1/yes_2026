"""
YES 2026 Summit - Production Configuration Module
Organized by VTU VRIF Belagavi
"""

import os
import urllib.parse
from pathlib import Path

# Load environment variables from .env if present
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_PATH, override=True)
except ImportError:
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip().strip("'\""))

# ----------------- SERVER & SECURITY ----------------- #
ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")
SECRET_KEY = os.environ.get("SECRET_KEY", "yes-2026-vrif-enterprise-secret-key-prod-belagavi")
SERVER_HOST = os.environ.get("HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("PORT", 5000))
HTTPS_PORT = int(os.environ.get("HTTPS_PORT", 5443))

# Admin Security Credentials
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "yes2026")

# ----------------- SUPABASE CREDENTIALS ----------------- #
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vlxktgfdwjtzomfsqbgt.supabase.co")
SUPABASE_PUBLISHABLE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or SUPABASE_SECRET_KEY or SUPABASE_PUBLISHABLE_KEY or ""
if not SUPABASE_SECRET_KEY and SUPABASE_KEY:
    SUPABASE_SECRET_KEY = SUPABASE_KEY

def normalize_database_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip().strip("'\"")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    try:
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname or ""
        if hostname and hostname not in ("localhost", "127.0.0.1"):
            query_params = urllib.parse.parse_qs(parsed.query)
            if "sslmode" not in query_params:
                delimiter = "&" if parsed.query else "?"
                url = f"{url}{delimiter}sslmode=require"
    except Exception:
        pass
    return url

raw_url = os.environ.get("SUPABASE_DB_URL") or os.environ.get("DATABASE_URL") or ""
if "[YOUR-PASSWORD]" in raw_url or "[PROJECT-REF]" in raw_url:
    raw_url = ""

DATABASE_URL = normalize_database_url(raw_url) if raw_url else ""

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
POSTGRES_DB = os.environ.get("POSTGRES_DB", "postgres")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")
POSTGRES_SSLMODE = os.environ.get("POSTGRES_SSLMODE", "require" if "supabase" in POSTGRES_HOST else "prefer")

DB_POOL_MIN = int(os.environ.get("DB_POOL_MIN", 2))
DB_POOL_MAX = int(os.environ.get("DB_POOL_MAX", 20))
DB_CONNECT_TIMEOUT = int(os.environ.get("DB_CONNECT_TIMEOUT", 10))

def is_supabase_configured() -> bool:
    if SUPABASE_URL and ("supabase.co" in SUPABASE_URL or "supabase.com" in SUPABASE_URL):
        return True
    if DATABASE_URL and ("supabase.co" in DATABASE_URL or "supabase.com" in DATABASE_URL or "pooler.supabase" in DATABASE_URL):
        return True
    return False

# ----------------- SMTP TRANSACTIONAL EMAIL CONFIG ----------------- #
def get_smtp_config() -> dict:
    """Dynamically resolves SMTP configuration from os.environ and .env file."""
    if not os.environ.get("SMTP_PASSWORD") and ENV_PATH.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=ENV_PATH, override=True)
        except Exception:
            pass

    enabled = os.environ.get("SMTP_ENABLED", "true").strip().lower() in ("true", "1", "yes")
    server = os.environ.get("SMTP_SERVER", "smtp.gmail.com").strip()
    port = int(os.environ.get("SMTP_PORT", 587))
    use_tls = os.environ.get("SMTP_USE_TLS", "true").strip().lower() in ("true", "1", "yes")
    username = os.environ.get("SMTP_USERNAME", "shanvtu@gmail.com").strip()
    password = os.environ.get("SMTP_PASSWORD", "sxcetlfvuzxpbpsj").strip().replace(" ", "")
    from_name = os.environ.get("SMTP_FROM_NAME", "YES 2026 • VTU VRIF Belagavi").strip()
    from_email = os.environ.get("SMTP_FROM_EMAIL", username).strip()

    return {
        "enabled": enabled,
        "server": server,
        "port": port,
        "use_tls": use_tls,
        "username": username,
        "password": password,
        "from_name": from_name,
        "from_email": from_email
    }

# Backward compatible module-level exports
_smtp_cfg = get_smtp_config()
SMTP_ENABLED = _smtp_cfg["enabled"]
SMTP_SERVER = _smtp_cfg["server"]
SMTP_PORT = _smtp_cfg["port"]
SMTP_USE_TLS = _smtp_cfg["use_tls"]
SMTP_USERNAME = _smtp_cfg["username"]
SMTP_PASSWORD = _smtp_cfg["password"]
SMTP_FROM_NAME = _smtp_cfg["from_name"]
SMTP_FROM_EMAIL = _smtp_cfg["from_email"]


