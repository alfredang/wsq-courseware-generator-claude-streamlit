"""Open browser for NotebookLM login. Auto-saves auth when login detected.
Clears old profile each time so user can login with a NEW account.
"""
import asyncio
import shutil
from pathlib import Path
from playwright.async_api import async_playwright

STORAGE_PATH = Path.home() / ".notebooklm" / "storage_state.json"
PROFILE_DIR = Path.home() / ".notebooklm" / "browser_profile"

async def main():
    STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Clear old browser profile so user starts fresh
    if PROFILE_DIR.exists():
        shutil.rmtree(PROFILE_DIR, ignore_errors=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    pw = await async_playwright().start()
    ctx = await pw.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=False,
        channel="chrome",
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
        ],
        ignore_default_args=["--enable-automation"],
    )

    page = ctx.pages[0] if ctx.pages else await ctx.new_page()
    await page.goto("https://accounts.google.com/signin")
    print("Browser opened — please login to your Google account.")

    # Wait for user to complete login (detect URL change away from accounts.google.com)
    for i in range(600):
        try:
            url = page.url
            # Detect if user finished Google sign-in
            if ("myaccount.google.com" in url or
                "notebooklm.google.com" in url or
                ("google.com" in url and "accounts.google.com" not in url and "signin" not in url)):
                print(f"Sign-in detected! Navigating to NotebookLM...")
                await page.goto("https://notebooklm.google.com")
                await asyncio.sleep(5)
                break
        except Exception:
            break  # Browser was closed
        await asyncio.sleep(1)
        if i > 0 and i % 30 == 0:
            print(f"  Waiting for login... ({i}s)")

    # Save storage state
    try:
        await ctx.storage_state(path=str(STORAGE_PATH))
        print(f"Authentication saved to {STORAGE_PATH}")
    except Exception:
        print("Browser closed before saving. Please try again.")

    try:
        await ctx.close()
    except Exception:
        pass
    await pw.stop()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
