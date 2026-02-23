"""
Batch authenticator for NotebookLM accounts.

Opens a Playwright Chrome browser for each unauthenticated account,
allowing the user to manually sign in. Saves per-account storage states.

Usage:
    python -m generate_slides.authenticate_accounts
    python -m generate_slides.authenticate_accounts --accounts 1-5
    python -m generate_slides.authenticate_accounts --all
"""

import json
import os
import pathlib
import shutil
import sys

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = pathlib.Path.home() / ".notebooklm" / "accounts"


def _get_accounts():
    """Load account list from environment variables."""
    emails_str = os.environ.get("NOTEBOOKLM_EMAILS", "")
    password = os.environ.get("NOTEBOOKLM_PASSWORD", "")
    if not emails_str:
        print("ERROR: NOTEBOOKLM_EMAILS not set in .env")
        sys.exit(1)
    emails = [e.strip() for e in emails_str.split(",") if e.strip()]
    accounts = []
    for email in emails:
        key = email.split("@")[0].replace(".", "_")
        accounts.append({"email": email, "password": password, "key": key})
    return accounts


def authenticate_account(acct: dict) -> bool:
    """Authenticate a single account via interactive browser login."""
    from playwright.sync_api import sync_playwright

    key = acct["key"]
    email = acct["email"]
    storage_dir = BASE_DIR / key
    profile_dir = storage_dir / "browser_profile"
    storage_path = storage_dir / "storage_state.json"

    # Clean browser profile for fresh login
    if profile_dir.exists():
        shutil.rmtree(profile_dir, ignore_errors=True)
    profile_dir.mkdir(parents=True, exist_ok=True)
    storage_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"  Authenticating: {email}")
    print(f"  Storage: {storage_path}")
    print(f"{'=' * 60}")
    print(f"\n  1. Sign in with: {email}")
    print(f"  2. Password: {acct['password']}")
    print(f"  3. Wait until you see the NotebookLM homepage")
    print(f"  4. Come back here and press ENTER\n")

    p = sync_playwright().start()
    browser = p.chromium.launch_persistent_context(
        str(profile_dir),
        headless=False,
        channel="chrome",
        args=[
            "--disable-blink-features=AutomationControlled",
            "--password-store=basic",
        ],
        ignore_default_args=["--enable-automation"],
    )
    page = browser.pages[0] if browser.pages else browser.new_page()
    page.goto("https://notebooklm.google.com/")

    input(f"  Press ENTER when {email} is signed in...")

    browser.storage_state(path=str(storage_path))
    print(f"  Saved: {storage_path}")
    browser.close()
    p.stop()
    return True


def main():
    accounts = _get_accounts()
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    # Parse --accounts flag (e.g., --accounts 1-5 or --accounts 3)
    account_range = None
    force_all = "--all" in sys.argv
    if "--accounts" in sys.argv:
        idx = sys.argv.index("--accounts")
        if idx + 1 < len(sys.argv):
            range_str = sys.argv[idx + 1]
            if "-" in range_str:
                start, end = range_str.split("-")
                account_range = (int(start) - 1, int(end))
            else:
                n = int(range_str)
                account_range = (n - 1, n)

    print(f"\nNotebookLM Account Authenticator")
    print(f"Found {len(accounts)} accounts in NOTEBOOKLM_EMAILS\n")

    authenticated = 0
    skipped = 0

    for i, acct in enumerate(accounts):
        if account_range and not (account_range[0] <= i < account_range[1]):
            continue

        storage_path = BASE_DIR / acct["key"] / "storage_state.json"

        if storage_path.exists() and not force_all:
            print(f"  [{i + 1}/{len(accounts)}] {acct['email']} — already authenticated, skipping")
            skipped += 1
            continue

        authenticate_account(acct)
        authenticated += 1

    print(f"\nDone! Authenticated: {authenticated}, Skipped: {skipped}")
    print(f"Total ready: {authenticated + skipped}/{len(accounts)}")


if __name__ == "__main__":
    main()
