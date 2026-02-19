"""Helper script to switch NotebookLM Google account using Chrome browser."""
from playwright.sync_api import sync_playwright
import pathlib
import shutil

# Delete old browser profile to start fresh
profile_dir = pathlib.Path.home() / '.notebooklm' / 'browser_profile'
if profile_dir.exists():
    shutil.rmtree(profile_dir, ignore_errors=True)
profile_dir.mkdir(parents=True, exist_ok=True)

print("Opening Google Chrome browser...")
print()
print("Steps:")
print("1. Sign in with your Google account")
print("2. Wait until you see the NotebookLM homepage")
print("3. Come back here and press ENTER")
print()

p = sync_playwright().start()
browser = p.chromium.launch_persistent_context(
    str(profile_dir),
    headless=False,
    channel="chrome",  # Use Google Chrome
    args=[
        "--disable-blink-features=AutomationControlled",
        "--password-store=basic",
    ],
    ignore_default_args=["--enable-automation"],
)
page = browser.pages[0] if browser.pages else browser.new_page()
page.goto('https://notebooklm.google.com/')

input("Press ENTER when you are signed in and see NotebookLM homepage...")

# Save auth
storage_path = pathlib.Path.home() / '.notebooklm' / 'storage_state.json'
browser.storage_state(path=str(storage_path))
print(f"\nAuthentication saved to: {storage_path}")
browser.close()
p.stop()
print("Done! You can now generate slides in the app.")
