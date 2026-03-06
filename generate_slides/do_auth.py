"""One-shot NotebookLM auth script — uses REAL Chrome, fresh profile, 10-min window."""

import shutil
import pathlib
import time
import json
import re
from playwright.sync_api import sync_playwright

NBLM_DIR = pathlib.Path.home() / ".notebooklm"
PROFILE_DIR = NBLM_DIR / "_auth_chrome"
STORAGE_PATH = NBLM_DIR / "storage_state.json"
ACCOUNTS_DIR = NBLM_DIR / "accounts"


def main():
    # Always start fresh
    if PROFILE_DIR.exists():
        shutil.rmtree(PROFILE_DIR, ignore_errors=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  NotebookLM Account Login (Real Chrome)")
    print("=" * 60)
    print()
    print("Opening Chrome — sign in with your Google account.")
    print("You have 10 minutes.")
    print()

    with sync_playwright() as p:
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

        page.goto(
            "https://accounts.google.com/AccountChooser"
            "?continue=https://notebooklm.google.com",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        print("Browser opened! Sign in now.\n")

        signed_in = False
        for i in range(600):  # 10 minutes
            try:
                for pg in browser.pages:
                    try:
                        if pg.is_closed():
                            continue
                        url = pg.url or ""
                        host = url.split("?")[0].lower()
                        if (
                            "notebooklm.google.com" in host
                            and "accounts.google" not in host
                        ):
                            time.sleep(3)
                            signed_in = True
                            page = pg
                            print(f"NotebookLM detected! URL: {url}")
                            break
                    except Exception:
                        continue
                if signed_in:
                    break
                if not browser.pages:
                    print("Browser was closed.")
                    break
            except Exception:
                pass
            time.sleep(1)
            if i > 0 and i % 30 == 0:
                print(f"  Waiting... ({i}s)")

        if signed_in:
            browser.storage_state(path=str(STORAGE_PATH))

            # Detect email
            state = json.loads(STORAGE_PATH.read_text())
            full = json.dumps(state)
            emails = set(
                re.findall(r"[\w.+-]+@[\w.-]+\.(?:com|sg|org|net|edu)", full)
            )
            email_str = ", ".join(sorted(emails)) if emails else "unknown"

            # Save per-account
            if emails:
                for email in sorted(emails):
                    prefix = email.split("@")[0].replace(".", "_")
                    acct_dir = ACCOUNTS_DIR / prefix
                    acct_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(
                        str(STORAGE_PATH), str(acct_dir / "storage_state.json")
                    )
                    print(f"  Saved: {email} -> {acct_dir}")
            else:
                prefix = f"account_{int(time.time())}"
                acct_dir = ACCOUNTS_DIR / prefix
                acct_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(
                    str(STORAGE_PATH), str(acct_dir / "storage_state.json")
                )
                print(f"  Saved to: {acct_dir}")

            print()
            print("=" * 60)
            print(f"  SUCCESS! Account: {email_str}")
            print("=" * 60)
        else:
            print("\nLogin not detected. Please try again.")

        try:
            browser.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
