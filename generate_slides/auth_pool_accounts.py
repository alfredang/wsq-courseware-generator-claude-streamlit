"""Authenticate multiple NotebookLM accounts using REAL Chrome + CDP + auto-fill.

Uses real Chrome browser (not Playwright Chromium) to bypass Google's
automation detection, then connects via CDP to auto-fill email/password.
"""

import subprocess
import shutil
import pathlib
import time
import json
import sys
import os
import asyncio
from playwright.async_api import async_playwright

ACCOUNTS = [
    ("training12.tertiaryinfotech@gmail.com", "Tertiary@888", "training12"),
    ("training13.tertiaryinfotech@gmail.com", "Tertiary@888", "training13"),
    ("training11.tertiaryinfotech@gmail.com", "Tertiary@888", "training11"),
]

# Allow selecting specific accounts via command line
if len(sys.argv) > 1:
    indices = [int(x) - 1 for x in sys.argv[1:]]
    ACCOUNTS = [ACCOUNTS[i] for i in indices if i < len(ACCOUNTS)]

NBLM_DIR = pathlib.Path.home() / ".notebooklm"
ACCOUNTS_DIR = NBLM_DIR / "accounts"


def find_chrome():
    """Find Chrome installation on Windows."""
    candidates = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def kill_chrome():
    """Kill existing Chrome to free port 9222."""
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True, text=True)
    time.sleep(2)


async def authenticate_account_cdp(email, password, account_key, chrome_path):
    """Authenticate one account using real Chrome + CDP + auto-fill."""
    base = ACCOUNTS_DIR / account_key
    storage_path = base / "storage_state.json"
    profile_dir = NBLM_DIR / f"_chrome_auth_{account_key}"

    base.mkdir(parents=True, exist_ok=True)

    # Clean profile for fresh login
    if profile_dir.exists():
        shutil.rmtree(profile_dir, ignore_errors=True)
    profile_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Authenticating: {email}")
    print(f"  Account key: {account_key}")
    print(f"  Storage: {storage_path}")
    print(f"{'='*60}")

    # Launch REAL Chrome with remote debugging
    print("  [1/6] Launching Chrome...", flush=True)
    proc = subprocess.Popen([
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-default-apps",
        "--disable-extensions",
        "https://accounts.google.com/signin/v2/identifier?continue=https://notebooklm.google.com",
    ])

    # Wait for Chrome CDP to be ready
    print("  [2/6] Connecting via CDP...", flush=True)
    connected = False
    for attempt in range(30):
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:9222/json", timeout=2)
            connected = True
            break
        except Exception:
            await asyncio.sleep(1)

    if not connected:
        print("  ERROR: Cannot connect to Chrome CDP")
        proc.terminate()
        return False

    success = False
    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        # Wait for page to load
        await asyncio.sleep(4)
        print(f"  Current URL: {page.url}", flush=True)

        # Step 1: Auto-fill email
        print("  [3/6] Filling email...", flush=True)
        try:
            await page.wait_for_selector('input[type="email"]', timeout=15000)
            # Type character by character (more human-like)
            email_input = page.locator('input[type="email"]')
            await email_input.click()
            await asyncio.sleep(0.5)
            await email_input.fill(email)
            await asyncio.sleep(1)

            # Click Next button
            next_btn = page.locator('#identifierNext')
            if await next_btn.count() > 0:
                await next_btn.click()
            else:
                next_btn = page.locator('button:has-text("Next")')
                await next_btn.first.click()
            await asyncio.sleep(4)
            print(f"  URL after email: {page.url}", flush=True)
        except Exception as e:
            print(f"  Email fill error: {e}", flush=True)

        # Step 2: Auto-fill password
        print("  [4/6] Filling password...", flush=True)
        try:
            # Wait for password field (may take a moment to appear)
            await page.wait_for_selector('input[type="password"]:visible', timeout=15000)
            pwd_input = page.locator('input[type="password"]:visible')
            await pwd_input.click()
            await asyncio.sleep(0.5)
            await pwd_input.fill(password)
            await asyncio.sleep(1)

            # Click Next button
            pwd_next = page.locator('#passwordNext')
            if await pwd_next.count() > 0:
                await pwd_next.click()
            else:
                pwd_next = page.locator('button:has-text("Next")')
                await pwd_next.first.click()
            await asyncio.sleep(5)
            print(f"  URL after password: {page.url}", flush=True)
        except Exception as e:
            print(f"  Password fill error: {e}", flush=True)

        # Step 3: Handle post-login prompts (Terms, "Not now", "I agree", etc.)
        print("  [5/6] Handling post-login prompts...", flush=True)
        for retry in range(5):
            await asyncio.sleep(2)
            current_url = page.url
            print(f"  Checking page: {current_url}", flush=True)

            # Check if already on NotebookLM
            if current_url.startswith("https://notebooklm.google.com"):
                print("  Already on NotebookLM!", flush=True)
                break

            # Try clicking common prompts
            try:
                # "I agree" / "Accept" buttons
                for selector in [
                    'button:has-text("I agree")',
                    'button:has-text("Accept")',
                    'button:has-text("Not now")',
                    'button:has-text("Continue")',
                    'button:has-text("Skip")',
                    'button:has-text("Done")',
                    '#confirm',
                    'button:has-text("Yes, I")',
                ]:
                    btn = page.locator(selector)
                    if await btn.count() > 0:
                        print(f"  Clicking: {selector}", flush=True)
                        await btn.first.click()
                        await asyncio.sleep(3)
                        break
            except Exception:
                pass

            # If on consent/terms page, try to navigate directly to NotebookLM
            if "consent" in current_url or "terms" in current_url:
                print("  On consent page, trying direct navigation...", flush=True)
                await page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)

        # Step 4: Wait for NotebookLM to fully load
        print("  [6/6] Waiting for NotebookLM...", flush=True)
        for elapsed in range(0, 120, 2):
            try:
                for pg in context.pages:
                    try:
                        url = pg.url or ""
                        if url.startswith("https://notebooklm.google.com"):
                            print(f"  NotebookLM loaded! ({elapsed}s)", flush=True)
                            await asyncio.sleep(3)

                            # Save storage state
                            state = await context.storage_state()
                            cookies = state.get("cookies", [])
                            has_sid = any(
                                c["name"] == "SID" and ".google.com" in c.get("domain", "")
                                for c in cookies
                            )

                            if not has_sid:
                                print(f"  Warning: No SID cookie ({len(cookies)} cookies total)")

                            # Save to account directory
                            storage_path.parent.mkdir(parents=True, exist_ok=True)
                            storage_path.write_text(json.dumps(state, indent=2))

                            # Also save to default location
                            default_storage = NBLM_DIR / "storage_state.json"
                            default_storage.write_text(json.dumps(state, indent=2))

                            print(f"  SUCCESS! {email} — {len(cookies)} cookies saved", flush=True)
                            success = True
                            break
                    except Exception:
                        continue
                if success:
                    break
            except Exception:
                pass
            await asyncio.sleep(2)
            if elapsed > 0 and elapsed % 30 == 0:
                # Log current URLs for debugging
                try:
                    urls = [pg.url for pg in context.pages if not pg.is_closed()]
                    print(f"  Still waiting... ({elapsed}s) — URLs: {urls}", flush=True)
                except Exception:
                    print(f"  Still waiting... ({elapsed}s)", flush=True)

        if not success:
            # Try one last time: navigate directly to NotebookLM
            try:
                print("  Last attempt: navigating directly to NotebookLM...", flush=True)
                await page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(5)
                if page.url.startswith("https://notebooklm.google.com"):
                    state = await context.storage_state()
                    storage_path.parent.mkdir(parents=True, exist_ok=True)
                    storage_path.write_text(json.dumps(state, indent=2))
                    default_storage = NBLM_DIR / "storage_state.json"
                    default_storage.write_text(json.dumps(state, indent=2))
                    print(f"  SUCCESS (on retry)! {email}", flush=True)
                    success = True
                else:
                    print(f"  FAILED: Final URL = {page.url}", flush=True)
            except Exception as e:
                print(f"  FAILED: {e}", flush=True)

    except Exception as e:
        print(f"  ERROR: {e}", flush=True)
    finally:
        try:
            await browser.close()
        except Exception:
            pass
        await pw.stop()

    # Kill Chrome and clean up
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

    # Clean temp profile
    try:
        shutil.rmtree(profile_dir, ignore_errors=True)
    except Exception:
        pass

    return success


async def main():
    chrome_path = find_chrome()
    if not chrome_path:
        print("ERROR: Google Chrome not found!")
        sys.exit(1)

    print(f"Chrome: {chrome_path}")
    print(f"Accounts to authenticate: {len(ACCOUNTS)}")
    ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)

    results = {}
    for email, password, key in ACCOUNTS:
        # Kill Chrome between accounts to free port 9222
        kill_chrome()
        ok = await authenticate_account_cdp(email, password, key, chrome_path)
        results[email] = ok

    print(f"\n{'='*60}")
    print("  RESULTS:")
    for email, ok in results.items():
        status = "OK" if ok else "FAILED"
        print(f"    {email}: {status}")

    # Show all authenticated accounts
    if ACCOUNTS_DIR.exists():
        print(f"\n  All authenticated accounts:")
        for d in sorted(ACCOUNTS_DIR.iterdir()):
            ss = d / "storage_state.json"
            if ss.exists():
                print(f"    [{d.name}] {ss}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
