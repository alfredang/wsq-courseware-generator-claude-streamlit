"""Auth script that waits for a signal file to save storage state."""
import shutil, pathlib, time, json, re, sys
from playwright.sync_api import sync_playwright

NBLM_DIR = pathlib.Path.home() / ".notebooklm"
PROFILE_DIR = NBLM_DIR / "_auth_chrome2"
STORAGE_PATH = NBLM_DIR / "storage_state.json"
ACCOUNTS_DIR = NBLM_DIR / "accounts"
SIGNAL_FILE = NBLM_DIR / "_save_now"

# Clean up
if PROFILE_DIR.exists():
    shutil.rmtree(PROFILE_DIR, ignore_errors=True)
PROFILE_DIR.mkdir(parents=True, exist_ok=True)
ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
if SIGNAL_FILE.exists():
    SIGNAL_FILE.unlink()

print("Opening Chrome for NotebookLM login...", flush=True)

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
    print("Browser open! Log in now.", flush=True)
    print(f"Waiting for signal file: {SIGNAL_FILE}", flush=True)

    # Wait for signal file (created externally when user confirms login)
    for i in range(600):
        if SIGNAL_FILE.exists():
            print("Signal received! Saving...", flush=True)
            break
        time.sleep(1)
        if i > 0 and i % 60 == 0:
            print(f"  Still waiting... ({i}s)", flush=True)

    # Save storage state
    browser.storage_state(path=str(STORAGE_PATH))
    state = json.loads(STORAGE_PATH.read_text())
    full_text = json.dumps(state)
    emails = set(re.findall(r"[\w.+-]+@[\w.-]+\.(?:com|sg|org|net|edu)", full_text))
    email_str = ", ".join(sorted(emails)) if emails else "unknown"

    for email in sorted(emails) if emails else []:
        prefix = email.split("@")[0].replace(".", "_")
        acct_dir = ACCOUNTS_DIR / prefix
        acct_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(STORAGE_PATH), str(acct_dir / "storage_state.json"))
        print(f"  Saved: {email} -> {acct_dir}", flush=True)

    if not emails:
        prefix = f"account_{int(time.time())}"
        acct_dir = ACCOUNTS_DIR / prefix
        acct_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(STORAGE_PATH), str(acct_dir / "storage_state.json"))
        print(f"  Saved to: {acct_dir}", flush=True)

    print(f"\nSUCCESS! Account: {email_str}", flush=True)
    try:
        browser.close()
    except:
        pass

# Clean signal
if SIGNAL_FILE.exists():
    SIGNAL_FILE.unlink()
