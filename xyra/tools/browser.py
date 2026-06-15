# ─────────────────────────────────────────────
#  XYRA — Browser Automation Tools
#  Exposes scraping, screenshots, and YouTube to LiveKit
# ─────────────────────────────────────────────

import os
import re
import asyncio
import logging
import webbrowser
import urllib.parse
from playwright.async_api import async_playwright

logger = logging.getLogger("xyra.tools.browser")

# Path constants
BASE_DIR          = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
USER_DATA_DIR     = os.path.join(BASE_DIR, "user_data")
SCREENSHOTS_DIR    = os.path.join(BASE_DIR, "screenshots")



# ── Screenshot ────────────────────────────────────────────────────────────────

async def browser_screenshot_tool(url: str) -> str:
    """
    Open any webpage and take a full-page screenshot.
    Use this when the user asks to see a website, capture a screen, or verify what is shown on a URL.
    """
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    filename = f"screenshot_{int(asyncio.get_event_loop().time())}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page    = await context.new_page()
        try:
            url_clean = url.strip()
            if not url_clean.startswith(("http://", "https://")):
                url_clean = "https://" + url_clean
            await page.goto(url_clean)
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=filepath, full_page=True)
            return f"✅ Screenshot saved to: {filepath}"
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return f"❌ Failed to capture screenshot: {e}"
        finally:
            await browser.close()


async def browser_scrape_text_tool(url: str) -> str:
    """
    Navigate to a URL and scrape clean, readable text content from the webpage.
    Use this when standard web search isn't enough and you need to read the full body of an article or site.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page    = await context.new_page()
        try:
            url_clean = url.strip()
            if not url_clean.startswith(("http://", "https://")):
                url_clean = "https://" + url_clean
            # Set a fast 8-second timeout for pages to prevent Voice Assistant lag
            await page.goto(url_clean, timeout=8000, wait_until="domcontentloaded")
            content = await page.locator("body").inner_text()
            content_clean = re.sub(r'\s+', ' ', content).strip()
            return f"📄 Scraped content from {url_clean}:\n\n" + content_clean[:4000]
        except Exception as e:
            logger.error(f"Error scraping text: {e}")
            return f"❌ Failed to scrape webpage: {e}"
        finally:
            await browser.close()


# ── YouTube ───────────────────────────────────────────────────────────────────

async def play_youtube_video_tool(query: str) -> str:
    """
    Open YouTube in a headed browser, search for the query, and click the first video result.
    Use this when Vickyy asks to play a video, song, or tutorial on YouTube.
    """
    p       = await async_playwright().start()
    browser = None
    try:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page    = await context.new_page()

        await page.goto("https://www.youtube.com/")
        await page.wait_for_selector('input#search', timeout=20000)

        search_input = page.locator('input#search').first
        await search_input.click()
        await search_input.fill(query)
        await asyncio.sleep(1)
        await search_input.press("Enter")
        await asyncio.sleep(3)

        first_video = page.locator('ytd-video-renderer a#video-title').first
        if await first_video.count() == 0:
            first_video = page.locator('a[href*="/watch?v="]').first

        if await first_video.count() == 0:
            await browser.close()
            await p.stop()
            return f"❌ Could not find any video results on YouTube for '{query}'."

        await first_video.click()
        return f"✅ Now playing the first YouTube result for '{query}'."
    except Exception as e:
        logger.error(f"Error playing YouTube video: {e}")
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        try:
            await p.stop()
        except Exception:
            pass
        return f"❌ Error playing YouTube video: {e}"


# ── Interactive Browsing ──────────────────────────────────────────────────────

def open_chrome_visibly(query_or_url: str) -> str:
    """
    Visually pop open a Chrome browser window on the user's screen.
    Use this EXACTLY when Vickyy says "show me websites", "open a website", 
    "let me see", or explicitly wants to visually browse online shopping, etc.
    If the input is a URL (e.g. github.com), it navigates there.
    If the input is a search query (e.g. 'online shopping sites'), it searches Google.
    Can accept a comma-separated list of URLs to open multiple tabs.
    """
    import urllib.parse
    targets = [t.strip() for t in query_or_url.split(',') if t.strip()]
    
    opened_list = []
    
    # If the user passed a search query with commas (e.g. "books, laptops, and more"),
    # we don't want to split it into 3 searches. So if the original string doesn't look like URLs,
    # we treat it as one search query.
    if ',' in query_or_url and not any('.' in t and ' ' not in t for t in targets):
        targets = [query_or_url.strip()]
        
    for target in targets:
        if target.startswith(('http://', 'https://')) or ('.' in target and ' ' not in target):
            url = target if target.startswith(('http://', 'https://')) else 'https://' + target
            webbrowser.open(url)
            opened_list.append(url)
        else:
            query_encoded = urllib.parse.quote(target)
            url = f"https://www.google.com/search?q={query_encoded}"
            webbrowser.open(url)
            opened_list.append(f"Search: {target}")
            
    if len(opened_list) == 1:
        return f"✅ Opened Chrome and navigated to: {opened_list[0]}"
    return f"✅ Opened Chrome with {len(opened_list)} tabs: " + ", ".join(opened_list)
