"""
Organizations Management Utilities

This module handles loading and saving organization data,
including company details and templates.
"""

import json
import os
from typing import List, Dict, Any

ORGANIZATIONS_FILE = "generate_ap_fg_lg_lp/utils/organizations.json"

def get_organizations() -> List[Dict[str, Any]]:
    """Load organizations from JSON file"""
    try:
        if os.path.exists(ORGANIZATIONS_FILE):
            with open(ORGANIZATIONS_FILE, 'r') as f:
                organizations = json.load(f)
                
            # Ensure all organizations have required fields
            for org in organizations:
                if "templates" not in org:
                    org["templates"] = {
                        "course_proposal": "",
                        "courseware": "",
                        "assessment": "",
                        "brochure": ""
                    }
                if "address" not in org:
                    org["address"] = ""
                    
            return organizations
    except Exception as e:
        print(f"Error loading organizations: {e}")
    
    return []

def save_organizations(organizations: List[Dict[str, Any]]) -> bool:
    """Save organizations to JSON file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(ORGANIZATIONS_FILE), exist_ok=True)
        
        with open(ORGANIZATIONS_FILE, 'w') as f:
            json.dump(organizations, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving organizations: {e}")
        return False

def get_organization_by_name(name: str) -> Dict[str, Any]:
    """Get specific organization by name"""
    organizations = get_organizations()
    for org in organizations:
        if org["name"] == name:
            return org
    return {}

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