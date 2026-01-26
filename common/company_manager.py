"""
Company Manager Utility

This module provides utilities for managing company selection
and template fallback functionality across all generation modules.
"""

import streamlit as st
from typing import Dict, Any, Optional
from generate_ap_fg_lg_lp.utils.organizations import get_organizations, get_default_organization, replace_company_branding

def get_selected_company() -> Dict[str, Any]:
    """Get the currently selected company from session state"""
    return st.session_state.get('selected_company', get_default_organization())

def get_company_template(template_type: str, company: Optional[Dict[str, Any]] = None) -> str:
    """
    Get company template path with fallback to Tertiary Infotech templates
    
    Args:
        template_type: Type of template ('course_proposal', 'courseware', 'assessment', 'brochure')
        company: Company dict (optional, uses selected company if not provided)
    
    Returns:
        Template path or empty string if not available
    """
    if company is None:
        company = get_selected_company()
    
    templates = company.get("templates", {})
    template_path = templates.get(template_type, "")
    
    # If company doesn't have specific template, use Tertiary Infotech template
    if not template_path:
        default_org = get_default_organization()
        default_templates = default_org.get("templates", {})
        template_path = default_templates.get(template_type, "")
    
    return template_path

def apply_company_branding(content: str, company: Optional[Dict[str, Any]] = None) -> str:
    """
    Apply company branding to content
    
    Args:
        content: Content to process
        company: Company dict (optional, uses selected company if not provided)
    
    Returns:
        Content with company branding applied
    """
    if company is None:
        company = get_selected_company()
    
    return replace_company_branding(content, company)

def get_company_info_display() -> Dict[str, str]:
    """Get formatted company information for display"""
    company = get_selected_company()
    
    return {
        "name": company.get("name", ""),
        "uen": company.get("uen", ""),
        "address": company.get("address", ""),
        "logo": company.get("logo", "")
    }

def show_company_info(show_in_sidebar: bool = False):
    """Show current company information - DISABLED"""
    # This function has been disabled per user request
    pass

def get_template_fallback_info(template_type: str) -> Dict[str, str]:
    """
    Get information about template fallback
    
    Args:
        template_type: Type of template to check
    
    Returns:
        Dict with template info and fallback status
    """
    company = get_selected_company()
    template_path = get_company_template(template_type)
    
    company_has_template = bool(company.get("templates", {}).get(template_type))
    using_fallback = not company_has_template
    
    return {
        "template_path": template_path,
        "using_fallback": using_fallback,
        "fallback_company": "Tertiary Infotech Academy Pte Ltd" if using_fallback else None,
        "company_name": company.get("name", "")
    }