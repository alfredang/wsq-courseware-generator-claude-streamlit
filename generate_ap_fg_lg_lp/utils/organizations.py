"""
Organizations Management Utilities

This module handles loading organization data from the Neon PostgreSQL database.
"""

from typing import List, Dict, Any
from company.database import (
    get_all_organizations,
    get_organization_by_name as db_get_organization_by_name,
    add_organization,
    update_organization_by_name,
    delete_organization_by_name
)


def get_organizations() -> List[Dict[str, Any]]:
    """Load organizations from database"""
    return get_all_organizations()


def save_organizations(organizations: List[Dict[str, Any]]) -> bool:
    """Save organizations to database (upsert)"""
    try:
        for org in organizations:
            existing = db_get_organization_by_name(org.get("name", ""))
            if existing:
                update_organization_by_name(org.get("name", ""), org)
            else:
                add_organization(org)
        return True
    except Exception as e:
        print(f"Error saving organizations: {e}")
        return False


def get_organization_by_name(name: str) -> Dict[str, Any]:
    """Get specific organization by name"""
    org = db_get_organization_by_name(name)
    return org if org else {}


def get_default_organization() -> Dict[str, Any]:
    """Get Tertiary Infotech as default organization"""
    organizations = get_organizations()
    for org in organizations:
        if "tertiary infotech" in org["name"].lower():
            return org

    # Return first organization if Tertiary Infotech not found
    if organizations:
        return organizations[0]

    # Fallback empty organization
    return {
        "name": "Tertiary Infotech Academy Pte Ltd",
        "uen": "201200696W",
        "logo": "common/logo/tertiary_infotech_pte_ltd.jpg",
        "address": "",
        "templates": {
            "course_proposal": "",
            "courseware": "",
            "assessment": "",
            "brochure": ""
        }
    }


def replace_company_branding(content: str, company: Dict[str, Any]) -> str:
    """Replace company branding placeholders in content"""
    replacements = {
        "{{COMPANY_NAME}}": company.get("name", ""),
        "{{COMPANY_UEN}}": company.get("uen", ""),
        "{{COMPANY_ADDRESS}}": company.get("address", ""),
        "{{COMPANY_LOGO}}": company.get("logo", ""),
        # Legacy support
        "Tertiary Infotech Pte Ltd": company.get("name", "Tertiary Infotech Academy Pte Ltd"),
        "201200696W": company.get("uen", "201200696W")
    }

    result = content
    for placeholder, replacement in replacements.items():
        result = result.replace(placeholder, replacement)

    return result
