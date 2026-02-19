"""
Database Module for Neon PostgreSQL Integration

This module handles all database operations for company/organization data.
Uses Neon PostgreSQL as the backend with connection pooling for performance.
"""

import os
import json
import threading
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Connection Pool (module-level singleton, thread-safe)
# ---------------------------------------------------------------------------

_pool: Optional[SimpleConnectionPool] = None
_pool_lock = threading.Lock()


def _get_pool() -> SimpleConnectionPool:
    """Get or create the connection pool (lazy init, thread-safe)."""
    global _pool
    if _pool is None or _pool.closed:
        with _pool_lock:
            if _pool is None or _pool.closed:
                database_url = os.environ.get("DATABASE_URL", "")
                if not database_url:
                    raise Exception("DATABASE_URL not configured in environment variables")
                _pool = SimpleConnectionPool(1, 5, database_url)
    return _pool


@contextmanager
def _get_conn():
    """Context manager that borrows a connection from the pool and returns it.
    Automatically handles stale/closed connections (common with Neon serverless)."""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        # Check if connection is alive (Neon may close idle connections)
        if conn.closed:
            pool.putconn(conn, close=True)
            conn = pool.getconn()
        yield conn
    except (psycopg2.InterfaceError, psycopg2.OperationalError):
        # Connection died mid-query — discard and re-raise so caller can retry
        try:
            pool.putconn(conn, close=True)
        except Exception:
            pass
        raise
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            pool.putconn(conn)
        except Exception:
            pass


def _normalize_path(path: str) -> str:
    """Normalize file path separators for cross-platform compatibility.
    Always uses forward slashes which work on both Windows and macOS/Linux."""
    return path.replace("\\", "/") if path else ""


def _row_to_org(row: dict) -> dict:
    """Convert a database row to an organization dict."""
    templates = row["templates"] if row["templates"] else {
        "courseware": "",
        "assessment": "",
        "brochure": ""
    }
    # Normalize template paths
    if isinstance(templates, dict):
        templates = {k: _normalize_path(v) if isinstance(v, str) else v for k, v in templates.items()}

    return {
        "id": row["id"],
        "name": row["name"],
        "uen": row["uen"] or "",
        "address": row["address"] or "",
        "logo": _normalize_path(row["logo"] or ""),
        "templates": templates,
        "company_url": row.get("company_url") or "",
        "ssg_url": row.get("ssg_url") or "",
        "email": row.get("email") or "",
    }


# Legacy compatibility
def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", "")


def get_connection():
    """Legacy: get a raw connection. Prefer _get_conn() context manager."""
    database_url = get_database_url()
    if not database_url:
        raise Exception("DATABASE_URL not configured in environment variables or Streamlit secrets")
    return psycopg2.connect(database_url)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SELECT_COLS = "id, name, uen, address, logo, templates, company_url, ssg_url, email"


def init_database():
    """Initialize database tables if they don't exist"""
    try:
        with _get_conn() as conn:
            cur = conn.cursor()
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS organizations (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    uen VARCHAR(50),
                    address TEXT,
                    logo TEXT,
                    templates JSONB DEFAULT '{{}}',
                    company_url TEXT DEFAULT '',
                    ssg_url TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            for col in ['company_url', 'ssg_url', 'email']:
                cur.execute(f"""
                    DO $$
                    BEGIN
                        ALTER TABLE organizations ADD COLUMN {col} TEXT DEFAULT '';
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END $$;
                """)
            conn.commit()
            cur.close()
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


# ---------------------------------------------------------------------------
# CRUD Operations
# ---------------------------------------------------------------------------

def get_all_organizations() -> List[Dict[str, Any]]:
    """Get all organizations from database"""
    try:
        with _get_conn() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(f"SELECT {_SELECT_COLS} FROM organizations ORDER BY name")
            rows = cur.fetchall()
            cur.close()
        return [_row_to_org(row) for row in rows]
    except Exception as e:
        print(f"Error getting organizations: {e}")
        return []


def get_organization_by_id(org_id: int) -> Optional[Dict[str, Any]]:
    """Get organization by ID"""
    try:
        with _get_conn() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(f"SELECT {_SELECT_COLS} FROM organizations WHERE id = %s", (org_id,))
            row = cur.fetchone()
            cur.close()
        return _row_to_org(row) if row else None
    except Exception as e:
        print(f"Error getting organization by ID: {e}")
        return None


def get_organization_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get organization by name"""
    try:
        with _get_conn() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(f"SELECT {_SELECT_COLS} FROM organizations WHERE name = %s", (name,))
            row = cur.fetchone()
            cur.close()
        return _row_to_org(row) if row else None
    except Exception as e:
        print(f"Error getting organization by name: {e}")
        return None


def _org_params(org: dict) -> tuple:
    """Extract common INSERT/UPDATE parameters from an org dict."""
    templates = org.get("templates", {"courseware": "", "assessment": "", "brochure": ""})
    # Normalize template paths before storing
    if isinstance(templates, dict):
        templates = {k: _normalize_path(v) if isinstance(v, str) else v for k, v in templates.items()}
    return (
        org.get("name", ""),
        org.get("uen", ""),
        org.get("address", ""),
        _normalize_path(org.get("logo", "")),
        json.dumps(templates),
        org.get("company_url", ""),
        org.get("ssg_url", ""),
        org.get("email", ""),
    )


def add_organization(org: Dict[str, Any]) -> bool:
    """Add new organization to database"""
    try:
        with _get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO organizations (name, uen, address, logo, templates, company_url, ssg_url, email)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, _org_params(org))
            conn.commit()
            cur.close()
        return True
    except Exception as e:
        print(f"Error adding organization: {e}")
        return False


def update_organization(org_id: int, org: Dict[str, Any]) -> bool:
    """Update existing organization"""
    try:
        with _get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE organizations
                SET name = %s, uen = %s, address = %s, logo = %s, templates = %s,
                    company_url = %s, ssg_url = %s, email = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, _org_params(org) + (org_id,))
            conn.commit()
            cur.close()
        return True
    except Exception as e:
        print(f"Error updating organization: {e}")
        return False


def update_organization_by_name(name: str, org: Dict[str, Any]) -> bool:
    """Update organization by name"""
    try:
        with _get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE organizations
                SET name = %s, uen = %s, address = %s, logo = %s, templates = %s,
                    company_url = %s, ssg_url = %s, email = %s, updated_at = CURRENT_TIMESTAMP
                WHERE name = %s
            """, _org_params(org) + (name,))
            conn.commit()
            cur.close()
        return True
    except Exception as e:
        print(f"Error updating organization by name: {e}")
        return False


def delete_organization(org_id: int) -> bool:
    """Delete organization by ID"""
    try:
        with _get_conn() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM organizations WHERE id = %s", (org_id,))
            conn.commit()
            cur.close()
        return True
    except Exception as e:
        print(f"Error deleting organization: {e}")
        return False


def delete_organization_by_name(name: str) -> bool:
    """Delete organization by name"""
    try:
        with _get_conn() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM organizations WHERE name = %s", (name,))
            conn.commit()
            cur.close()
        return True
    except Exception as e:
        print(f"Error deleting organization by name: {e}")
        return False


def migrate_from_json(json_file: str) -> bool:
    """Migrate organizations from JSON file to database"""
    try:
        init_database()

        if not os.path.exists(json_file):
            print(f"JSON file not found: {json_file}")
            return False

        with open(json_file, 'r') as f:
            organizations = json.load(f)

        with _get_conn() as conn:
            cur = conn.cursor()
            for org in organizations:
                cur.execute("""
                    INSERT INTO organizations (name, uen, address, logo, templates, company_url, ssg_url, email)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        uen = EXCLUDED.uen,
                        address = EXCLUDED.address,
                        logo = EXCLUDED.logo,
                        templates = EXCLUDED.templates,
                        company_url = EXCLUDED.company_url,
                        ssg_url = EXCLUDED.ssg_url,
                        email = EXCLUDED.email,
                        updated_at = CURRENT_TIMESTAMP
                """, _org_params(org))
            conn.commit()
            cur.close()

        print(f"Successfully migrated {len(organizations)} organizations to database")
        return True
    except Exception as e:
        print(f"Error migrating from JSON: {e}")
        return False


def search_organizations(query: str) -> List[Dict[str, Any]]:
    """Search organizations by name, UEN, or address"""
    try:
        with _get_conn() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            search_pattern = f"%{query}%"
            cur.execute(f"""
                SELECT {_SELECT_COLS}
                FROM organizations
                WHERE name ILIKE %s OR uen ILIKE %s OR address ILIKE %s
                ORDER BY name
            """, (search_pattern, search_pattern, search_pattern))
            rows = cur.fetchall()
            cur.close()
        return [_row_to_org(row) for row in rows]
    except Exception as e:
        print(f"Error searching organizations: {e}")
        return []
