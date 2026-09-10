"""
YES 2026 Summit - Database Connection & Pool Manager
VTU's Visvesvaraya Research and Innovation Foundation (VRIF), Belagavi
"""

import time
import logging
from contextlib import contextmanager
from backend.config import (
    DATABASE_URL, POSTGRES_HOST, POSTGRES_PORT,
    POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_SSLMODE,
    DB_POOL_MIN, DB_POOL_MAX, DB_CONNECT_TIMEOUT
)

logger = logging.getLogger("yes2026.database.connection")

USE_POSTGRES = False
IS_SUPABASE = False
pg_pool = None

def init_postgres_pool(target_url=None, host=None, port=None, dbname=None, user=None, password=None, sslmode=None):
    try:
        import psycopg2
        from psycopg2 import pool
    except ImportError:
        logger.info("[Database Pool] psycopg2 library not installed. Operating on Supabase Cloud REST.")
        return None, False

    url = target_url or DATABASE_URL
    is_sb = False

    if url:
        if any(h in url.lower() for h in ("supabase.co", "supabase.com", "pooler.supabase")):
            is_sb = True
        
        test_conn = psycopg2.connect(url, connect_timeout=DB_CONNECT_TIMEOUT)
        test_conn.close()

        p = pool.ThreadedConnectionPool(
            minconn=DB_POOL_MIN,
            maxconn=DB_POOL_MAX,
            dsn=url
        )
        return p, is_sb
    elif host and password:
        if "supabase" in host.lower():
            is_sb = True

        test_conn = psycopg2.connect(
            host=host,
            port=port or 5432,
            dbname=dbname or "postgres",
            user=user or "postgres",
            password=password,
            sslmode=sslmode or "require",
            connect_timeout=DB_CONNECT_TIMEOUT
        )
        test_conn.close()

        p = pool.ThreadedConnectionPool(
            minconn=DB_POOL_MIN,
            maxconn=DB_POOL_MAX,
            host=host,
            port=port or 5432,
            dbname=dbname or "postgres",
            user=user or "postgres",
            password=password,
            sslmode=sslmode or "require"
        )
        return p, is_sb
    else:
        raise ValueError("No database URL or PostgreSQL credentials provided.")

try:
    if (DATABASE_URL and len(DATABASE_URL.strip()) > 15) or (POSTGRES_HOST and POSTGRES_PASSWORD):
        pool_res = init_postgres_pool(
            target_url=DATABASE_URL,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            sslmode=POSTGRES_SSLMODE
        )
        if pool_res and pool_res[0]:
            pg_pool, IS_SUPABASE = pool_res
            USE_POSTGRES = True
            logger.info(f"[Database Pool] Initialized connection pool for {'Supabase Cloud' if IS_SUPABASE else 'PostgreSQL'}.")
        else:
            USE_POSTGRES = False
            IS_SUPABASE = False
            pg_pool = None
except Exception as err:
    USE_POSTGRES = False
    IS_SUPABASE = False
    pg_pool = None
    logger.info(f"[Database Pool] Direct PostgreSQL pool inactive ({err}). Operating on Supabase Cloud REST engine.")

@contextmanager
def get_connection():
    """Yields a verified live database connection from the pool."""
    if USE_POSTGRES and pg_pool:
        conn = None
        for attempt in range(3):
            try:
                conn = pg_pool.getconn()
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                break
            except Exception:
                if conn:
                    try:
                        pg_pool.putconn(conn, close=True)
                    except Exception:
                        pass
                    conn = None
        try:
            yield conn
        finally:
            if conn:
                try:
                    pg_pool.putconn(conn)
                except Exception:
                    pass
    else:
        yield None
