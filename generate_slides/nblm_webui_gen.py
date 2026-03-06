"""Generate NotebookLM slides via Web UI automation (bypasses API rate limits).

Creates a notebook, adds text source, generates slide deck via the web UI,
downloads the PDF, and extracts images. Works when the API is rate-limited.
"""
import asyncio
import pathlib
import time
import logging
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

NBLM_DIR = pathlib.Path.home() / ".notebooklm"
PROFILE_DIR = NBLM_DIR / "browser_profile"


def _extract_images_from_pdf(pdf_path: str, output_dir: pathlib.Path, max_images: int) -> list:
    """Extract page images from PDF, skip cover+summary."""
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    total = doc.page_count
    if total == 0:
        return []
    start = 1 if total > 2 else 0
    end = total - 1 if total > 2 else total
    images = []
    for idx in range(start, min(end, start + max_images)):
        page = doc[idx]
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        img_path = str(output_dir / f"slide_{idx:03d}.png")
        pix.save(img_path)
        images.append(img_path)
    doc.close()
    return images


async def generate_topic_images_webui(
    topic_title: str,
    source_text: str,
    topic_key: str,
    n_images: int,
    progress_callback=None,
) -> list:
    """Generate fresh NotebookLM images for one topic via web UI.

    Returns list of image paths, or empty list on failure.
    """
    from playwright.async_api import async_playwright

    cache_dir = pathlib.Path.home() / "AppData" / "Local" / "Temp" / "nblm_matched_images" / topic_key
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Check cache
    cached = sorted(cache_dir.glob("slide_*.png"))
    if cached:
        logger.info(f"[{topic_key}] Using {len(cached)} cached images")
        return [str(p) for p in cached[:n_images]]

    pdf_path = cache_dir / f"{topic_key}.pdf"

    async with async_playwright() as p:
        try:
            if progress_callback:
                progress_callback(f"[{topic_key}] Opening NotebookLM browser...", None)

            browser = await p.chromium.launch_persistent_context(
                str(PROFILE_DIR),
                headless=False,
                channel="chrome",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--no-default-browser-check",
                ],
                ignore_default_args=["--enable-automation"],
                viewport={"width": 1280, "height": 900},
            )
            page = browser.pages[0] if browser.pages else await browser.new_page()

            # 1. Open NotebookLM
            await page.goto("https://notebooklm.google.com", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(4)
            if "accounts.google" in page.url:
                logger.error(f"[{topic_key}] Not logged in")
                await browser.close()
                return []

            # 2. Create notebook
            if progress_callback:
                progress_callback(f"[{topic_key}] Creating notebook...", None)
            await page.locator('button:has-text("Create new")').first.click(timeout=10000)
            await asyncio.sleep(4)

            # 3. Click "Copied text"
            for sel in ['button:has-text("Copied text")', ':text("Copied text")']:
                try:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=3000):
                        await el.click()
                        await asyncio.sleep(2)
                        break
                except:
                    continue

            # 4. Fill title
            try:
                title_el = page.locator("input").first
                await title_el.fill(f"Slides: {topic_title[:80]}", timeout=5000)
            except:
                pass

            # 5. Fill content in the "Paste text here" textarea
            if progress_callback:
                progress_callback(f"[{topic_key}] Adding source content...", None)
            try:
                textarea = page.locator('textarea[placeholder="Paste text here"]').first
                await textarea.fill(source_text[:50000], timeout=5000)
            except:
                try:
                    textarea = page.locator("textarea").last
                    await textarea.fill(source_text[:50000], timeout=5000)
                except:
                    pass

            await asyncio.sleep(1)

            # 6. Click Insert
            try:
                await page.locator('button:has-text("Insert")').first.click(timeout=5000)
            except:
                pass
            await asyncio.sleep(5)

            # 7. Click "Slide deck" in the Studio panel
            if progress_callback:
                progress_callback(f"[{topic_key}] Generating slides...", None)

            slide_clicked = False
            for sel in [
                'button:has-text("Slide deck")',
                ':text("Slide deck")',
                'button:has-text("Slides")',
            ]:
                try:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=3000):
                        await el.click()
                        slide_clicked = True
                        logger.info(f"[{topic_key}] Clicked Slide deck button")
                        break
                except:
                    continue

            if not slide_clicked:
                logger.error(f"[{topic_key}] Could not find Slide deck button")
                await browser.close()
                return []

            await asyncio.sleep(5)

            # 8. Look for Generate/Create button if needed
            for sel in [
                'button:has-text("Generate")',
                'button:has-text("Create")',
                'button:has-text("Start")',
            ]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=3000):
                        await btn.click()
                        logger.info(f"[{topic_key}] Clicked Generate")
                        break
                except:
                    continue

            # 9. Wait for generation and download
            if progress_callback:
                progress_callback(f"[{topic_key}] Waiting for NotebookLM to generate...", None)

            start = time.time()
            downloaded = False
            timeout_sec = 180

            while time.time() - start < timeout_sec:
                # Check for download button or PDF link
                for sel in [
                    'button:has-text("Download")',
                    'a:has-text("Download")',
                    '[aria-label*="ownload"]',
                    'button:has-text("download")',
                ]:
                    try:
                        btn = page.locator(sel).first
                        if await btn.is_visible(timeout=2000):
                            logger.info(f"[{topic_key}] Download button found!")
                            async with page.expect_download(timeout=30000) as dl:
                                await btn.click()
                            download = await dl.value
                            await download.save_as(str(pdf_path))
                            downloaded = True
                            break
                    except:
                        continue

                if downloaded:
                    break

                elapsed = int(time.time() - start)
                if elapsed % 20 == 0 and elapsed > 0:
                    if progress_callback:
                        progress_callback(f"[{topic_key}] Still generating... ({elapsed}s)", None)
                await asyncio.sleep(5)

            await browser.close()

            if downloaded and pdf_path.exists():
                if progress_callback:
                    progress_callback(f"[{topic_key}] Extracting images from PDF...", None)
                images = _extract_images_from_pdf(str(pdf_path), cache_dir, n_images)
                logger.info(f"[{topic_key}] Got {len(images)} fresh images!")
                return images
            else:
                logger.warning(f"[{topic_key}] Generation did not complete")
                return []

        except Exception as e:
            logger.error(f"[{topic_key}] Web UI error: {e}")
            try:
                await browser.close()
            except:
                pass
            return []
