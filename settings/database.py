"""
Database Module for Neon PostgreSQL Integration

This module handles all database operations for company/organization data.
Uses Neon PostgreSQL as the backend.
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def get_connection():
    """Get database connection"""
    if not DATABASE_URL:
        raise Exception("DATABASE_URL not configured in environment variables")
    return psycopg2.connect(DATABASE_URL)


def init_database():
    """Initialize database tables if they don't exist"""
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Create organizations table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                uen VARCHAR(50),
                address TEXT,
                logo TEXT,
                templates JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


def get_all_organizations() -> List[Dict[str, Any]]:
    """Get all organizations from database"""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT id, name, uen, address, logo, templates
            FROM organizations
            ORDER BY name
        """)

        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Convert to list of dicts with proper structure
        organizations = []
        for row in rows:
            org = {
                "id": row["id"],
                "name": row["name"],
                "uen": row["uen"] or "",
                "address": row["address"] or "",
                "logo": row["logo"] or "",
                "templates": row["templates"] if row["templates"] else {
                    "course_proposal": "",
                    "courseware": "",
                    "assessment": "",
                    "brochure": ""
                }
            }
            organizations.append(org)

        return organizations
    except Exception as e:
        print(f"Error getting organizations: {e}")
        return []


def get_organization_by_id(org_id: int) -> Optional[Dict[str, Any]]:
    """Get organization by ID"""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT id, name, uen, address, logo, templates
            FROM organizations
            WHERE id = %s
        """, (org_id,))

        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            return {
                "id": row["id"],
                "name": row["name"],
                "uen": row["uen"] or "",
                "address": row["address"] or "",
                "logo": row["logo"] or "",
                "templates": row["templates"] if row["templates"] else {
                    "course_proposal": "",
                    "courseware": "",
                    "assessment": "",
                    "brochure": ""
                }
            }
        return None
    except Exception as e:
        print(f"Error getting organization by ID: {e}")
        return None


def get_organization_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get organization by name"""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT id, name, uen, address, logo, templates
            FROM organizations
            WHERE name = %s
        """, (name,))

        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            return {
                "id": row["id"],
                "name": row["name"],
                "uen": row["uen"] or "",
                "address": row["address"] or "",
                "logo": row["logo"] or "",
                "templates": row["templates"] if row["templates"] else {
                    "course_proposal": "",
                    "courseware": "",
                    "assessment": "",
                    "brochure": ""
                }
            }
        return None
    except Exception as e:
        print(f"Error getting organization by name: {e}")
        return None


def add_organization(org: Dict[str, Any]) -> bool:
    """Add new organization to database"""
    try:
        conn = get_connection()
        cur = conn.cursor()

        templates = org.get("templates", {
            "course_proposal": "",
            "courseware": "",
            "assessment": "",
            "brochure": ""
        })

        cur.execute("""
            INSERT INTO organizations (name, uen, address, logo, templates)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            org.get("name", ""),
            org.get("uen", ""),
            org.get("address", ""),
            org.get("logo", ""),
            json.dumps(templates)
        ))

        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding organization: {e}")
        return False


def update_organization(org_id: int, org: Dict[str, Any]) -> bool:
    """Update existing organization"""
    try:
        conn = get_connection()
        cur = conn.cursor()

        templates = org.get("templates", {
            "course_proposal": "",
            "courseware": "",
            "assessment": "",
            "brochure": ""
        })

        cur.execute("""
            UPDATE organizations
            SET name = %s, uen = %s, address = %s, logo = %s, templates = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            org.get("name", ""),
            org.get("uen", ""),
            org.get("address", ""),
            org.get("logo", ""),
            json.dumps(templates),
            org_id
        ))

        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating organization: {e}")
        return False


def update_organization_by_name(name: str, org: Dict[str, Any]) -> bool:
    """Update organization by name"""
    try:
        conn = get_connection()
        cur = conn.cursor()

        templates = org.get("templates", {
            "course_proposal": "",
            "courseware": "",
            "assessment": "",
            "brochure": ""
        })

        cur.execute("""
            UPDATE organizations
            SET name = %s, uen = %s, address = %s, logo = %s, templates = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE name = %s
        """, (
            org.get("name", ""),
            org.get("uen", ""),
            org.get("address", ""),
            org.get("logo", ""),
            json.dumps(templates),
            name
        ))

        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating organization by name: {e}")
        return False


def delete_organization(org_id: int) -> bool:
    """Delete organization by ID"""
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM organizations WHERE id = %s", (org_id,))

        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting organization: {e}")
        return False


def delete_organization_by_name(name: str) -> bool:
    """Delete organization by name"""
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM organizations WHERE name = %s", (name,))

        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting organization by name: {e}")
        return False


def migrate_from_json(json_file: str) -> bool:
    """Migrate organizations from JSON file to database"""
    try:
        # Initialize database first
        init_database()

        # Load JSON data
        if not os.path.exists(json_file):
            print(f"JSON file not found: {json_file}")
            return False

        with open(json_file, 'r') as f:
            organizations = json.load(f)

        conn = get_connection()
        cur = conn.cursor()

        for org in organizations:
            templates = org.get("templates", {
                "course_proposal": "",
                "courseware": "",
                "assessment": "",
                "brochure": ""
            })

            # Use upsert to handle duplicates
            cur.execute("""
                INSERT INTO organizations (name, uen, address, logo, templates)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    uen = EXCLUDED.uen,
                    address = EXCLUDED.address,
                    logo = EXCLUDED.logo,
                    templates = EXCLUDED.templates,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                org.get("name", ""),
                org.get("uen", ""),
                org.get("address", ""),
                org.get("logo", ""),
                json.dumps(templates)
            ))

        conn.commit()
        cur.close()
        conn.close()
        print(f"Successfully migrated {len(organizations)} organizations to database")
        return True
    except Exception as e:
        print(f"Error migrating from JSON: {e}")
        return False


def search_organizations(query: str) -> List[Dict[str, Any]]:
    """Search organizations by name, UEN, or address"""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        search_pattern = f"%{query}%"
        cur.execute("""
            SELECT id, name, uen, address, logo, templates
            FROM organizations
            WHERE name ILIKE %s OR uen ILIKE %s OR address ILIKE %s
            ORDER BY name
        """, (search_pattern, search_pattern, search_pattern))

        rows = cur.fetchall()
        cur.close()
        conn.close()

        organizations = []
        for row in rows:
            org = {
                "id": row["id"],
                "name": row["name"],
                "uen": row["uen"] or "",
                "address": row["address"] or "",
                "logo": row["logo"] or "",
                "templates": row["templates"] if row["templates"] else {
                    "course_proposal": "",
                    "courseware": "",
                    "assessment": "",
                    "brochure": ""
                }
            }
            organizations.append(org)

        return organizations
    except Exception as e:
        print(f"Error searching organizations: {e}")
        return []
