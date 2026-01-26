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
          from generate_ap_fg_lg_lp.utils.organization_utils import load_organizations, add_organization
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

ORG_FILE = "generate_ap_fg_lg_lp/utils/organizations.json"

class Organization(BaseModel):
    name: str
    uen: str
    logo: Optional[str] = None

def load_organizations():
    if os.path.exists(ORG_FILE):
        with open(ORG_FILE, "r") as f:
            return json.load(f)
    return []

def save_organizations(org_list):
    with open(ORG_FILE, "w") as f:
        json.dump(org_list, f, indent=4)

def add_organization(org):
    org_list = load_organizations()
    org_list.append(org.dict())
    save_organizations(org_list)

def update_organization(index, org):
    org_list = load_organizations()
    org_list[index] = org.dict()
    save_organizations(org_list)

def delete_organization(index):
    org_list = load_organizations()
    org_list.pop(index)
    save_organizations(org_list)
