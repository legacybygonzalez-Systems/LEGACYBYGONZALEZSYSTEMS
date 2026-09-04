import logging
import random
import time
from typing import List
from urllib.parse import urlparse

import requests

from .models import AgentLead
from .sites.base import SiteAdapter

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def check_robots_allows(url: str) -> bool:
    """Best-effort robots.txt check. Returns True if disallow rules for this
    path were NOT found (or robots.txt couldn't be fetched). This is
    informational only -- it does not enforce anything."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        resp = requests.get(robots_url, timeout=10, headers={"User-Agent": DEFAULT_USER_AGENT})
        if resp.status_code != 200:
            return True
        disallowed = [
            line.split(":", 1)[1].strip()
            for line in resp.text.splitlines()
            if line.lower().startswith("disallow:")
        ]
        path = parsed.path or "/"
        return not any(path.startswith(rule) for rule in disallowed if rule)
    except requests.RequestException:
        return True


def scrape_leads(
    adapter: SiteAdapter,
    max_pages: int = 5,
    min_delay: float = 3.0,
    max_delay: float = 7.0,
    headless: bool = True,
) -> List[AgentLead]:
    """Drive a headless browser through an adapter's search results pages
    and return deduplicated leads.

    Requires `playwright` and its browser binaries
    (`python -m playwright install chromium`).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "playwright is required for scraping. Install with "
            "`pip install playwright && python -m playwright install chromium`"
        ) from exc

    first_url = adapter.build_search_url(1)
    if not check_robots_allows(first_url):
        logger.warning(
            "robots.txt appears to disallow %s -- proceeding only because "
            "you explicitly configured this target. Consider a different "
            "source if this is a concern.",
            first_url,
        )

    leads: List[AgentLead] = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(user_agent=DEFAULT_USER_AGENT)
        page = context.new_page()

        for page_num in range(1, max_pages + 1):
            url = adapter.build_search_url(page_num)
            logger.info("Fetching page %d: %s", page_num, url)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)
            except Exception:
                logger.exception("Failed to load %s", url)
                break

            html = page.content()
            page_leads = adapter.parse_listing_page(html)
            if not page_leads:
                logger.info("No leads found on page %d -- stopping.", page_num)
                break

            new_count = 0
            for lead in page_leads:
                key = lead.dedupe_key()
                if key in seen:
                    continue
                seen.add(key)
                leads.append(lead)
                new_count += 1
            logger.info("Page %d: %d new leads (%d total)", page_num, new_count, len(leads))

            if not adapter.has_next_page(html):
                logger.info("No further pages detected -- stopping.")
                break

            time.sleep(random.uniform(min_delay, max_delay))

        browser.close()

    return leads
