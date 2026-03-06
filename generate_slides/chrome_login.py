"""
Login to NotebookLM using REAL Chrome browser (bypasses Google's automation detection).

How it works:
1. Launches Chrome as a normal process (NOT through Playwright)
2. User logs in manually — Google sees a real browser, no blocking
3. Cookies are extracted via Chrome DevTools Protocol (CDP)
4. Saved to ~/.notebooklm/ for NotebookLM slide generation

Usage: uv run python generate_slides/chrome_login.py [account_name]
"""

import subprocess
import time
import json
import pathlib
import asyncio
import shutil
import sys
import os


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


async def poll_for_login(account_name, timeout=300):
    """Poll Chrome via CDP for successful Google login, then save cookies."""
    from playwright.async_api import async_playwright

    base_dir = pathlib.Path.home() / ".notebooklm"
    storage_path = base_dir / "storage_state.json"
    account_storage = base_dir / "accounts" / account_name / "storage_state.json"

    # Wait for Chrome CDP to be ready
    print("Connecting to Chrome via CDP...")
    for attempt in range(30):
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:9222/json", timeout=2)
            print("  Connected!")
            break
        except Exception:
            await asyncio.sleep(1)
    else:
        print("ERROR: Cannot connect to Chrome on port 9222")
        return False

    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        print("\n" + "=" * 50)
        print("Please sign in with your Google account in Chrome.")
        print("=" * 50 + "\n")

        # Poll for SID cookie (indicates successful Google login)
        for elapsed in range(0, timeout, 3):
            try:
                storage = await context.storage_state()
                cookies = storage.get("cookies", [])

                has_sid = any(
                    c["name"] == "SID" and ".google.com" in c.get("domain", "")
                    for c in cookies
                )

                if has_sid:
                    print(f"\nGoogle login detected! ({len(cookies)} cookies)")

                    # Navigate to NotebookLM to get all needed cookies
                    print("Navigating to NotebookLM to complete setup...")
                    try:
                        await page.goto(
                            "https://notebooklm.google.com/",
                            wait_until="networkidle",
                            timeout=30000,
                        )
                    except Exception:
                        # Even on timeout, try to save what we have
                        pass
                    await asyncio.sleep(3)

                    # Re-capture cookies after NotebookLM load
                    storage = await context.storage_state()

                    # Save to main location
                    storage_path.parent.mkdir(parents=True, exist_ok=True)
                    storage_path.write_text(json.dumps(storage, indent=2))

                    # Save to account directory
                    account_storage.parent.mkdir(parents=True, exist_ok=True)
                    account_storage.write_text(json.dumps(storage, indent=2))

                    total = len(storage.get("cookies", []))
                    print(f"\nSaved {total} cookies to:")
                    print(f"  {storage_path}")
                    print(f"  {account_storage}")
                    return True

            except Exception as e:
                err = str(e)
                if "closed" in err.lower() or "disconnect" in err.lower():
                    print("Browser was closed.")
                    return False

            await asyncio.sleep(3)
            if elapsed > 0 and elapsed % 30 == 0:
                print(f"  Still waiting for login... ({elapsed}s)")

        print(f"\nTimeout after {timeout}s.")
        return False

    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        try:
            await browser.close()
        except Exception:
            pass
        await pw.stop()


def main():
    account_name = sys.argv[1] if len(sys.argv) > 1 else "training2"

    chrome_path = find_chrome()
    if not chrome_path:
        print("ERROR: Google Chrome not found!")
        sys.exit(1)

    print(f"Chrome: {chrome_path}")

    # Kill existing Chrome to free port 9222
    print("Closing existing Chrome instances...")
    subprocess.run(
        ["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True, text=True
    )
    time.sleep(2)

    # Clean profile for fresh login
    profile_dir = pathlib.Path.home() / ".notebooklm" / f"chrome_login_{account_name}"
    if profile_dir.exists():
        shutil.rmtree(profile_dir, ignore_errors=True)
    profile_dir.mkdir(parents=True, exist_ok=True)

    # Launch REAL Chrome (not Playwright's Chromium)
    print(f"\nOpening Chrome for '{account_name}' login...")
    proc = subprocess.Popen(
        [
            chrome_path,
            "--remote-debugging-port=9222",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "https://accounts.google.com/signin",
        ]
    )

    try:
        success = asyncio.run(poll_for_login(account_name, timeout=300))
    except KeyboardInterrupt:
        print("\nCancelled.")
        success = False
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    if success:
        print(f"\nSUCCESS! Account '{account_name}' is ready for NotebookLM.")
    else:
        print(f"\nFailed. Please try again.")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
