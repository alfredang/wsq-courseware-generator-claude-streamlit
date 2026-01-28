"""
Admin Authentication Module

Simple authentication for protecting Settings pages.
Admin credentials are stored in SQLite database.
Initial setup requires ADMIN_USERNAME and ADMIN_PASSWORD in .streamlit/secrets.toml or environment variables.

Author: Wong Xin Ping
Date: 26 January 2026
"""

import streamlit as st
import hashlib
import os

from settings.api_database import (
    verify_admin_password,
    admin_credentials_exist,
    set_admin_credentials,
    get_admin_credentials_from_db,
)


def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get('admin_authenticated', False)


def logout():
    """Log out the admin user"""
    st.session_state['admin_authenticated'] = False
    st.session_state['admin_username'] = None


def _get_initial_credentials():
    """Get initial credentials from secrets/env for first-time setup"""
    try:
        username = st.secrets.get("ADMIN_USERNAME", os.environ.get("ADMIN_USERNAME", ""))
        password = st.secrets.get("ADMIN_PASSWORD", os.environ.get("ADMIN_PASSWORD", ""))
    except Exception:
        username = os.environ.get("ADMIN_USERNAME", "")
        password = os.environ.get("ADMIN_PASSWORD", "")
    return username, password


def login_page():
    """Display login page and handle authentication"""
    # Check if admin credentials exist in database
    if not admin_credentials_exist():
        # First-time setup - try to get from secrets/env
        username, password = _get_initial_credentials()
        if username and password:
            set_admin_credentials(username, password)
            st.info("Admin credentials initialized from configuration.")
        else:
            # Show setup form
            st.markdown("### Initial Admin Setup")
            st.warning("No admin credentials found. Please set up admin account.")
            st.caption("You can also set ADMIN_USERNAME and ADMIN_PASSWORD in .streamlit/secrets.toml or environment variables.")

            with st.form("admin_setup_form"):
                new_username = st.text_input("Username", placeholder="Enter admin username")
                new_password = st.text_input("Password", type="password", placeholder="Enter admin password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password")

                submitted = st.form_submit_button("Create Admin Account", type="primary")

                if submitted:
                    if not new_username or not new_password:
                        st.error("Username and password are required")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters")
                    else:
                        if set_admin_credentials(new_username, new_password):
                            st.success("Admin account created successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to create admin account")
            return

    # Normal login flow
    st.markdown("### Admin Login")
    st.caption("Enter admin credentials to access settings")

    with st.form("admin_login_form"):
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")

        col1, col2 = st.columns([1, 3])
        with col1:
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

        if submitted:
            if verify_admin_password(username, password):
                st.session_state['admin_authenticated'] = True
                st.session_state['admin_username'] = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")


def require_auth(page_function):
    """Decorator/wrapper to require authentication for a page"""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            login_page()
            return None
        return page_function(*args, **kwargs)
    return wrapper


def show_logout_button():
    """Show logout button in sidebar or page"""
    if is_authenticated():
        username = st.session_state.get('admin_username', 'Admin')
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"Logged in as: **{username}**")
        with col2:
            if st.button("Logout", key="logout_btn", use_container_width=True):
                logout()
                st.rerun()


def change_password_form():
    """Display form to change admin password"""
    if not is_authenticated():
        return

    st.markdown("### Change Password")

    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")

        submitted = st.form_submit_button("Change Password", type="primary")

        if submitted:
            username = st.session_state.get('admin_username', '')
            if not verify_admin_password(username, current_password):
                st.error("Current password is incorrect")
            elif new_password != confirm_password:
                st.error("New passwords do not match")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters")
            else:
                if set_admin_credentials(username, new_password):
                    st.success("Password changed successfully!")
                else:
                    st.error("Failed to change password")
