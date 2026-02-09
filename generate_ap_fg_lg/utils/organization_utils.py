"""
File: organization_utils.py

===============================================================================
Organization Utilities Module
===============================================================================
Description:
    This module provides utility functions for managing organization data in the Courseware system.
    It defines an Organization Pydantic model and functions to load, save, add, update, and delete
    organization records stored in a JSON file. These functions facilitate consistent management of
    organization details such as name, UEN, and logo.

Main Functionalities:
    • Organization (BaseModel):
          A Pydantic model representing an organization with fields for name, UEN, and an optional logo.
    • load_organizations():
          Reads and returns the list of organization records from a JSON file.
    • save_organizations(org_list):
          Saves the provided list of organization records to the JSON file with proper indentation.
    • add_organization(org):
          Appends a new organization to the existing list and saves the updated list.
    • update_organization(index, org):
          Updates the organization record at the specified index and saves the changes.
    • delete_organization(index):
          Removes the organization record at the specified index from the list and saves the updated list.

Dependencies:
    - Standard Libraries: json, os, typing (Optional)
    - Pydantic: For data validation and model creation.

Usage:
    - Import the functions to manage organization records in your application.
      Example:
          from generate_ap_fg_lg.utils.organization_utils import load_organizations, add_organization
          organizations = load_organizations()
          add_organization(new_org)

Author:
    Derrick Lim
Date:
    3 March 2025
===============================================================================
"""

import json
import os
from typing import Optional
from pydantic import BaseModel

ORG_FILE = "generate_ap_fg_lg/utils/organizations.json"

class Organization(BaseModel):
    name: str
    uen: str
    logo: Optional[str] = None

def load_organizations():
    # First try to load from JSON file
    if os.path.exists(ORG_FILE):
        with open(ORG_FILE, "r") as f:
            return json.load(f)
    # Fall back to database if JSON file doesn't exist
    try:
        from company.database import get_all_organizations
        return get_all_organizations()
    except Exception as e:
        print(f"Error loading organizations from database: {e}")
        return []

def save_organizations(org_list):
    # Save to JSON file
    with open(ORG_FILE, "w") as f:
        json.dump(org_list, f, indent=4)

def _use_database():
    """Check if we should use the database (when JSON file doesn't exist)"""
    return not os.path.exists(ORG_FILE)

def add_organization(org):
    if _use_database():
        try:
            from company.database import add_organization as db_add_organization
            db_add_organization(org.dict())
            return
        except Exception as e:
            print(f"Error adding organization to database: {e}")
    org_list = load_organizations()
    org_list.append(org.dict())
    save_organizations(org_list)

def update_organization(index, org):
    if _use_database():
        try:
            from company.database import get_all_organizations, update_organization_by_name
            orgs = get_all_organizations()
            if index < len(orgs):
                old_name = orgs[index]["name"]
                update_organization_by_name(old_name, org.dict())
                return
        except Exception as e:
            print(f"Error updating organization in database: {e}")
    org_list = load_organizations()
    org_list[index] = org.dict()
    save_organizations(org_list)

def delete_organization(index):
    if _use_database():
        try:
            from company.database import get_all_organizations, delete_organization_by_name
            orgs = get_all_organizations()
            if index < len(orgs):
                name = orgs[index]["name"]
                delete_organization_by_name(name)
                return
        except Exception as e:
            print(f"Error deleting organization from database: {e}")
    org_list = load_organizations()
    org_list.pop(index)
    save_organizations(org_list)
