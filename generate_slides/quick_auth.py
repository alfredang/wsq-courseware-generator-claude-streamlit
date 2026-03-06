"""Quick auth: Opens a FRESH browser for NotebookLM account login.

Always clears old browser profile so you can switch accounts freely.
Opens Google Account Chooser -> you pick/login -> session saved.

Multi-account support:
- Each account is saved to ~/.notebooklm/accounts/<email>/storage_state.json
- Also saved to ~/.notebooklm/storage_state.json as default
- The generation pipeline rotates between accounts when one is rate-limited

Usage:
    python -m generate_slides.quick_auth
    # or
    uv run python -m generate_slides.quick_auth
"""

import shutil
import pathlib
import sys
import time
import json
import re
from playwright.sync_api import sync_playwright

NBLM_DIR = pathlib.Path.home() / ".notebooklm"
STORAGE_PATH = NBLM_DIR / "storage_state.json"
ACCOUNTS_DIR = NBLM_DIR / "accounts"
PROFILE_DIR = NBLM_DIR / "_auth_profile"


def log(msg):
    print(msg, flush=True)


def _detect_email(storage_path):
    """Detect Google account email from storage state cookies."""
    try:
        state = json.loads(pathlib.Path(storage_path).read_text())
        full_text = json.dumps(state)
        emails = set(re.findall(r'[\w.+-]+@(?:gmail|google)\.com', full_text))
        return sorted(emails) if emails else []
    except Exception:
        return []


def list_accounts():
    """List all authenticated NotebookLM accounts."""
    accounts = []
    # Check default
    if STORAGE_PATH.exists():
        emails = _detect_email(STORAGE_PATH)
        accounts.append(("default", STORAGE_PATH, emails))
    # Check account-specific dirs
    if ACCOUNTS_DIR.exists():
        for d in sorted(ACCOUNTS_DIR.iterdir()):
            ss = d / "storage_state.json"
            if ss.exists():
                emails = _detect_email(ss)
                accounts.append((d.name, ss, emails))
    return accounts


def main():
    # Always start fresh — delete old browser profile
    if PROFILE_DIR.exists():
        shutil.rmtree(PROFILE_DIR, ignore_errors=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    NBLM_DIR.mkdir(parents=True, exist_ok=True)
    ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)

    # Show existing accounts
    existing = list_accounts()
    if existing:
        log("Existing authenticated accounts:")
        for name, path, emails in existing:
            email_str = ", ".join(emails) if emails else "unknown"
            log(f"  [{name}] {email_str}")
        log("")

    log("=" * 60)
    log("  NotebookLM Account Login")
    log("=" * 60)
    log("")
    log("Opening a FRESH browser - sign in with the account you want.")
    log("The session will be saved automatically when you reach NotebookLM.")
    log("")

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch_persistent_context(
                str(PROFILE_DIR),
                headless=False,
                channel="chrome",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--password-store=basic",
                ],
                ignore_default_args=["--enable-automation"],
            )
            page = browser.pages[0] if browser.pages else browser.new_page()

            # Go to Account Chooser which redirects to NotebookLM after login
            log("Opening Google Account Chooser...")
            page.goto(
                "https://accounts.google.com/AccountChooser"
                "?continue=https://notebooklm.google.com",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            log("Browser opened! Sign in with your Google account.")
            log("Waiting for NotebookLM to load...\n")

            # Poll until user reaches NotebookLM homepage
            # Check ALL pages/tabs, not just the first one
            signed_in = False
            for i in range(600):  # Up to 10 minutes
                try:
                    # Check all open pages/tabs
                    for p in browser.pages:
                        try:
                            if p.is_closed():
                                continue
                            url = p.url or ""
                            url_lower = url.lower()

                            # Detect NotebookLM page (check host only, not query params)
                            url_host_path = url.split("?")[0].lower()
                            if "notebooklm.google.com" in url_host_path and "accounts.google" not in url_host_path:
                                time.sleep(2)
                                signed_in = True
                                page = p  # Use this page for reference
                                log(f"NotebookLM loaded! URL: {url}")
                                break

                            # Also detect if user is past Google login (on any Google page, not accounts)
                            # and has been waiting a long time — auto-navigate to NotebookLM
                            if i > 60 and "google.com" in url_lower and "accounts.google" not in url_lower and "notebooklm" not in url_lower:
                                log(f"  Detected Google login complete. Navigating to NotebookLM...")
                                p.goto("https://notebooklm.google.com", wait_until="domcontentloaded", timeout=30000)
                                time.sleep(3)
                                new_url = p.url or ""
                                if "notebooklm.google.com" in new_url.split("?")[0].lower():
                                    signed_in = True
                                    page = p
                                    log(f"NotebookLM loaded! URL: {new_url}")
                                    break
                        except Exception:
                            continue

                    if signed_in:
                        break

                    # Check if all pages are closed
                    if not browser.pages:
                        log("Browser was closed.")
                        break

                except Exception:
                    pass  # Page might be navigating

                time.sleep(1)
                if i > 0 and i % 15 == 0:
                    log(f"  Still waiting... ({i}s)")

            if signed_in:
                # Save as default
                browser.storage_state(path=str(STORAGE_PATH))

                # Detect account email and save to account-specific dir
                emails = _detect_email(STORAGE_PATH)
                account_email = ", ".join(emails) if emails else "unknown"

                # Save to accounts/<email_prefix>/
                if emails:
                    for email in emails:
                        prefix = email.split("@")[0].replace(".", "_")
                        acct_dir = ACCOUNTS_DIR / prefix
                        acct_dir.mkdir(parents=True, exist_ok=True)
                        acct_ss = acct_dir / "storage_state.json"
                        shutil.copy2(str(STORAGE_PATH), str(acct_ss))
                        log(f"  Saved account: {email} -> {acct_ss}")

                log("")
                log("=" * 60)
                log(f"  SUCCESS! Account saved for slide generation.")
                log(f"  Account: {account_email}")
                log(f"  Saved to: {STORAGE_PATH}")
                log("=" * 60)
                log("")

                # Show all accounts now
                all_accts = list_accounts()
                if len(all_accts) > 1:
                    log(f"You now have {len(all_accts)} account(s) available:")
                    for name, path, acct_emails in all_accts:
                        email_str = ", ".join(acct_emails) if acct_emails else "unknown"
                        log(f"  [{name}] {email_str}")
                    log("")
                    log("The pipeline will rotate between accounts if one is rate-limited.")

                log("")
                log("You can now generate slides in the Streamlit app.")
                log("To add another account, run this script again and login with a different Google account.")
            else:
                log("\nCould not detect NotebookLM login. Please try again.")

            try:
                time.sleep(1)
                browser.close()
            except Exception:
                pass

        except Exception as e:
            log(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
