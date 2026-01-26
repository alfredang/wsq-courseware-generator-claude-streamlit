"""
Company Settings Management Module

This module provides UI for managing company details:
- Company name, UEN, address
- Company logos
- Document templates
"""

import streamlit as st
import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any
from PIL import Image

from generate_ap_fg_lg_lp.utils.organizations import get_organizations, save_organizations


def company_management_app():
    """Company Management page"""
    st.title("🏢 Company Management")
    manage_company_settings()


def backup_company_files(company: Dict) -> bool:
    """
    Move company files to backup folder before deletion
    Returns True if successful, False otherwise
    """
    try:
        # Create timestamped backup directory
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        company_name_clean = company['name'].lower().replace(' ', '_').replace('/', '_').replace('\\', '_')
        backup_dir = f"company/deleted_companies/{timestamp}_{company_name_clean}"
        os.makedirs(backup_dir, exist_ok=True)

        files_moved = []

        # Backup logo file
        logo_path = company.get('logo', '')
        if logo_path and os.path.exists(logo_path):
            logo_backup_dir = os.path.join(backup_dir, 'logo')
            os.makedirs(logo_backup_dir, exist_ok=True)
            logo_filename = os.path.basename(logo_path)
            backup_logo_path = os.path.join(logo_backup_dir, logo_filename)
            shutil.move(logo_path, backup_logo_path)
            files_moved.append(f"Logo: {logo_path} → {backup_logo_path}")

        # Backup template files
        templates = company.get('templates', {})
        if templates:
            template_backup_dir = os.path.join(backup_dir, 'templates')
            os.makedirs(template_backup_dir, exist_ok=True)

            for template_type, template_path in templates.items():
                if template_path and os.path.exists(template_path):
                    template_filename = os.path.basename(template_path)
                    backup_template_path = os.path.join(template_backup_dir, template_filename)
                    shutil.move(template_path, backup_template_path)
                    files_moved.append(f"{template_type}: {template_path} → {backup_template_path}")

        # Remove empty template directory if it exists
        template_dir = f"company/templates/{company_name_clean}"
        if os.path.exists(template_dir) and not os.listdir(template_dir):
            os.rmdir(template_dir)

        # Create a metadata file in backup folder
        metadata = {
            "company_name": company['name'],
            "uen": company.get('uen', ''),
            "deleted_at": timestamp,
            "files_moved": files_moved
        }

        metadata_path = os.path.join(backup_dir, 'backup_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        return True

    except Exception as e:
        st.error(f"Error backing up company files: {e}")
        return False


def display_company_list(organizations: List[Dict]):
    """Display searchable list of all companies"""

    # Search box
    search_query = st.text_input(
        "🔍 Search Companies",
        placeholder="Search by name, UEN, or address...",
        key="company_search"
    )

    # Filter companies based on search
    if search_query:
        query_lower = search_query.lower()
        filtered_orgs = [
            org for org in organizations
            if query_lower in org.get("name", "").lower()
            or query_lower in org.get("uen", "").lower()
            or query_lower in org.get("address", "").lower()
        ]
    else:
        filtered_orgs = organizations

    # Display count
    st.caption(f"Showing {len(filtered_orgs)} of {len(organizations)} companies")

    if not filtered_orgs:
        st.info("No companies found matching your search.")
        return

    # Display as table/list
    for idx, company in enumerate(filtered_orgs):
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

            with col1:
                st.markdown(f"**{company['name']}**")
                st.caption(f"UEN: {company.get('uen', 'N/A')}")

            with col2:
                address = company.get('address', '')
                if address:
                    st.caption(address[:50] + "..." if len(address) > 50 else address)
                else:
                    st.caption("No address")

            with col3:
                # Show logo and template status
                has_logo = "✅" if company.get('logo') else "❌"
                templates = company.get('templates', {})
                template_count = sum(1 for v in templates.values() if v)
                st.caption(f"Logo: {has_logo} | Templates: {template_count}/4")

            with col4:
                # Find original index for editing
                original_idx = organizations.index(company)
                if st.button("✏️", key=f"edit_btn_{idx}", help="Edit company"):
                    st.session_state['edit_company_idx'] = original_idx
                    st.session_state['company_view'] = 'edit'
                    st.rerun()

            st.divider()


def manage_company_settings():
    """Manage Company Details"""

    # Load current organizations
    try:
        organizations = get_organizations()
    except Exception as e:
        st.error(f"Error loading organizations from database: {e}")
        organizations = []

    # Initialize view state
    if 'company_view' not in st.session_state:
        st.session_state['company_view'] = 'list'

    # View selector using columns with buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📋 Company List", use_container_width=True,
                     type="primary" if st.session_state['company_view'] == 'list' else "secondary"):
            st.session_state['company_view'] = 'list'
            st.rerun()
    with col2:
        if st.button("✏️ Edit Company", use_container_width=True,
                     type="primary" if st.session_state['company_view'] == 'edit' else "secondary"):
            st.session_state['company_view'] = 'edit'
            st.rerun()
    with col3:
        if st.button("➕ Add New Company", use_container_width=True,
                     type="primary" if st.session_state['company_view'] == 'add' else "secondary"):
            st.session_state['company_view'] = 'add'
            st.rerun()

    st.markdown("---")

    # Display based on current view
    if st.session_state['company_view'] == 'list':
        display_company_list(organizations)

    elif st.session_state['company_view'] == 'edit':
        st.subheader("Select Company to Edit")

        if organizations:
            company_names = [org["name"] for org in organizations]

            # Use session state index if set from list view
            default_idx = st.session_state.get('edit_company_idx', 0)
            if default_idx >= len(organizations):
                default_idx = 0

            selected_company_idx = st.selectbox(
                "Choose a company:",
                range(len(company_names)),
                format_func=lambda x: company_names[x],
                index=default_idx
            )

            if selected_company_idx is not None and selected_company_idx < len(organizations):
                edit_company_form(organizations, selected_company_idx)
        else:
            st.info("No companies found. Add a new company first.")

    elif st.session_state['company_view'] == 'add':
        st.subheader("Add New Company")
        add_company_form(organizations)


def edit_company_form(organizations: List[Dict], company_idx: int):
    """Form to edit existing company"""
    company = organizations[company_idx]

    st.subheader(f"Edit: {company['name']}")

    with st.form(f"edit_company_{company_idx}"):
        # Company details
        new_name = st.text_input("Company Name", value=company["name"])
        new_uen = st.text_input("UEN", value=company["uen"])
        new_address = st.text_area("Address", value=company.get("address", ""))

        # Logo upload
        st.write("Company Logo")
        current_logo_path = company.get("logo", "")

        if current_logo_path and os.path.exists(current_logo_path):
            try:
                image = Image.open(current_logo_path)
                st.image(image, caption="Current Logo", width=200)
            except:
                st.warning("Could not display current logo")

        uploaded_logo = st.file_uploader(
            "Upload new logo (optional)",
            type=['png', 'jpg', 'jpeg'],
            help="Leave empty to keep current logo"
        )

        # Template management
        st.write("Templates")
        templates = company.get("templates", {})

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Course Proposal Template**")
            if templates.get("course_proposal"):
                st.success(f"✅ Current: {templates.get('course_proposal').split('/')[-1]}")
            cp_template_file = st.file_uploader("Upload Course Proposal Template", type=['docx', 'doc'], key=f"cp_template_{company_idx}")

            st.write("**Assessment Template**")
            if templates.get("assessment"):
                st.success(f"✅ Current: {templates.get('assessment').split('/')[-1]}")
            assessment_template_file = st.file_uploader("Upload Assessment Template", type=['docx', 'doc'], key=f"assessment_template_{company_idx}")

        with col2:
            st.write("**Courseware Template**")
            if templates.get("courseware"):
                st.success(f"✅ Current: {templates.get('courseware').split('/')[-1]}")
            courseware_template_file = st.file_uploader("Upload Courseware Template", type=['docx', 'doc'], key=f"courseware_template_{company_idx}")

            st.write("**Brochure Template**")
            if templates.get("brochure"):
                st.success(f"✅ Current: {templates.get('brochure').split('/')[-1]}")
            brochure_template_file = st.file_uploader("Upload Brochure Template", type=['docx', 'doc'], key=f"brochure_template_{company_idx}")

        # Submit button
        submitted = st.form_submit_button("💾 Update Company", type="primary")

        if submitted:
            # Update company data
            updated_company = {
                "name": new_name,
                "uen": new_uen,
                "address": new_address,
                "logo": company["logo"],  # Keep existing logo path initially
                "templates": company.get("templates", {})  # Keep existing templates initially
            }

            # Handle logo upload
            if uploaded_logo:
                logo_path = save_company_logo(uploaded_logo, new_name)
                if logo_path:
                    updated_company["logo"] = logo_path

            # Handle template uploads
            template_files = {
                "course_proposal": cp_template_file,
                "courseware": courseware_template_file,
                "assessment": assessment_template_file,
                "brochure": brochure_template_file
            }

            for template_type, template_file in template_files.items():
                if template_file:
                    template_path = save_company_template(template_file, new_name, template_type)
                    if template_path:
                        updated_company["templates"][template_type] = template_path

            # Update the organization in the list
            organizations[company_idx] = updated_company

            # Save to file
            if save_organizations(organizations):
                st.success(f"✅ Company '{new_name}' updated successfully!")
                # Clear cache to refresh sidebar company list
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("❌ Error updating company. Please try again.")

    # Delete company button (separate from form)
    delete_button_pressed = st.button(f"🗑️ Delete {company['name']}", type="secondary")

    if delete_button_pressed:
        if st.session_state.get(f"confirm_delete_{company_idx}", False):
            # Actually delete
            company_name = company['name']  # Store name before deletion

            # Backup company files before deletion
            backup_success = backup_company_files(company)

            if backup_success:
                # Remove from organizations list
                organizations.pop(company_idx)

                # Clear any session state that might reference old indices
                keys_to_remove = [key for key in st.session_state.keys() if key.startswith('confirm_delete_')]
                for key in keys_to_remove:
                    del st.session_state[key]

                if save_organizations(organizations):
                    st.session_state[f'delete_success_{company_idx}'] = f"✅ Company '{company_name}' deleted successfully! Files backed up to company/deleted_companies/"
                    # Clear cache to refresh sidebar company list
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ Error deleting company from database.")
            else:
                st.error("❌ Error backing up company files. Deletion cancelled for safety.")
        else:
            # Show confirmation
            st.session_state[f"confirm_delete_{company_idx}"] = True
            st.warning("⚠️ Click delete again to confirm removal. Files will be moved to backup folder.")

    # Show delete success message below the button if it exists
    if f'delete_success_{company_idx}' in st.session_state:
        st.success(st.session_state[f'delete_success_{company_idx}'])
        del st.session_state[f'delete_success_{company_idx}']


def add_company_form(organizations: List[Dict]):
    """Form to add new company"""

    # Initialize form fields with session state for clearing
    if 'clear_form' not in st.session_state:
        st.session_state.clear_form = False

    with st.form("add_new_company", clear_on_submit=False):
        st.subheader("New Company Details")

        # Company details - use empty values when form needs to be cleared
        company_name = st.text_input(
            "Company Name *",
            value="" if st.session_state.clear_form else st.session_state.get('temp_company_name', ''),
            placeholder="Enter company name"
        )
        company_uen = st.text_input(
            "UEN *",
            value="" if st.session_state.clear_form else st.session_state.get('temp_company_uen', ''),
            placeholder="Enter UEN number"
        )
        company_address = st.text_area(
            "Address",
            value="" if st.session_state.clear_form else st.session_state.get('temp_company_address', ''),
            placeholder="Enter company address (optional)"
        )

        # Logo upload
        uploaded_logo = st.file_uploader(
            "Upload company logo",
            type=['png', 'jpg', 'jpeg'],
            help="Optional: Upload company logo",
            key="company_logo_upload"
        )

        # Template management
        st.write("Templates (Optional)")
        col1, col2 = st.columns(2)
        with col1:
            cp_template_file = st.file_uploader("Course Proposal Template", type=['docx', 'doc'], key="new_cp_template")
            assessment_template_file = st.file_uploader("Assessment Template", type=['docx', 'doc'], key="new_assessment_template")
        with col2:
            courseware_template_file = st.file_uploader("Courseware Template", type=['docx', 'doc'], key="new_courseware_template")
            brochure_template_file = st.file_uploader("Brochure Template", type=['docx', 'doc'], key="new_brochure_template")

        # Submit button
        submitted = st.form_submit_button("➕ Add Company", type="primary")

        if submitted:
            if company_name and company_uen:
                # Create new company
                new_company = {
                    "name": company_name,
                    "uen": company_uen,
                    "address": company_address,
                    "logo": "",
                    "templates": {
                        "course_proposal": "",
                        "courseware": "",
                        "assessment": "",
                        "brochure": ""
                    }
                }

                # Handle logo upload
                if uploaded_logo:
                    logo_path = save_company_logo(uploaded_logo, company_name)
                    if logo_path:
                        new_company["logo"] = logo_path

                # Handle template uploads
                template_files = {
                    "course_proposal": cp_template_file,
                    "courseware": courseware_template_file,
                    "assessment": assessment_template_file,
                    "brochure": brochure_template_file
                }

                for template_type, template_file in template_files.items():
                    if template_file:
                        template_path = save_company_template(template_file, company_name, template_type)
                        if template_path:
                            new_company["templates"][template_type] = template_path

                # Add to organizations
                organizations.append(new_company)

                # Save to file
                if save_organizations(organizations):
                    # Store success message to show after rerun
                    st.session_state['add_company_success'] = f"✅ Company '{company_name}' added successfully!"
                    # Clear form fields by setting flag
                    st.session_state.clear_form = True
                    # Clear any temporary values
                    for key in ['temp_company_name', 'temp_company_uen', 'temp_company_address']:
                        if key in st.session_state:
                            del st.session_state[key]
                    # Clear cache to refresh sidebar company list
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ Error adding company. Please try again.")
            else:
                st.error("❌ Please fill in required fields: Company Name and UEN")

    # Reset clear form flag after displaying empty form
    if st.session_state.clear_form:
        st.session_state.clear_form = False

    # Show success message below the form if company was just added
    if 'add_company_success' in st.session_state:
        st.success(st.session_state['add_company_success'])
        # Clear the success message after showing it
        del st.session_state['add_company_success']


def save_company_logo(uploaded_file, company_name: str) -> str:
    """Save uploaded logo and return path"""
    try:
        # Create logo directory if it doesn't exist
        logo_dir = "company/logo"
        os.makedirs(logo_dir, exist_ok=True)

        # Generate filename
        file_extension = uploaded_file.name.split('.')[-1].lower()
        clean_name = company_name.lower().replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"{clean_name}.{file_extension}"
        file_path = os.path.join(logo_dir, filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        return file_path
    except Exception as e:
        st.error(f"Error saving logo: {e}")
        return ""


def save_company_template(uploaded_file, company_name: str, template_type: str) -> str:
    """Save uploaded template and return path"""
    try:
        # Create templates directory if it doesn't exist
        templates_dir = f"company/templates/{company_name.lower().replace(' ', '_')}"
        os.makedirs(templates_dir, exist_ok=True)

        # Generate filename
        file_extension = uploaded_file.name.split('.')[-1].lower()
        filename = f"{template_type}_template.{file_extension}"
        file_path = os.path.join(templates_dir, filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        return file_path
    except Exception as e:
        st.error(f"Error saving {template_type} template: {e}")
        return ""
