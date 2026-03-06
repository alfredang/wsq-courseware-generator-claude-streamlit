"""Open existing NotebookLM notebooks in browser for manual slide generation.
The notebooks already have sources loaded - just need to generate slides.
"""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

PROFILE_DIR = Path.home() / ".notebooklm" / "browser_profile"

# Existing notebooks with sources loaded (training8 account)
LU1_NB = "a39c75ce-6e09-4d98-bcd5-0e48edc3a771"
LU2A_NB = "4eb8026b-7469-482e-9d31-ea672d695a20"


def log(msg):
    print(msg, flush=True)


async def main():
    log("Starting browser...")
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

    # Open LU1
    page1 = ctx.pages[0] if ctx.pages else await ctx.new_page()
    url1 = f"https://notebooklm.google.com/notebook/{LU1_NB}"
    log(f"Opening LU1: {url1}")
    await page1.goto(url1, timeout=60000, wait_until="domcontentloaded")
    await asyncio.sleep(3)

    if "accounts.google.com" in page1.url:
        log("ERROR: Not logged in! Run quick_login.py first.")
        await ctx.close()
        await pw.stop()
        return

    log(f"LU1 loaded at: {page1.url}")

    # Open LU2-A in new tab
    page2 = await ctx.new_page()
    url2 = f"https://notebooklm.google.com/notebook/{LU2A_NB}"
    log(f"Opening LU2-A: {url2}")
    await page2.goto(url2, timeout=60000, wait_until="domcontentloaded")
    await asyncio.sleep(3)
    log(f"LU2-A loaded at: {page2.url}")

    log("")
    log("=== BOTH NOTEBOOKS ARE OPEN ===")
    log("Instructions:")
    log("  1. Delete any failed/stuck slide decks (click Delete)")
    log("  2. Click 'Slide Deck' to start generation")
    log("  3. Wait for generation to complete")
    log("")
    log("Browser will stay open. Close the browser window when done.")

    # Keep alive until browser closes
    try:
        while True:
            await asyncio.sleep(5)
            try:
                _ = page1.url
            except Exception:
                break
    except KeyboardInterrupt:
        pass

    try:
        await ctx.close()
    except Exception:
        pass
    await pw.stop()
    log("Browser closed. Done!")


if __name__ == "__main__":
    asyncio.run(main())
