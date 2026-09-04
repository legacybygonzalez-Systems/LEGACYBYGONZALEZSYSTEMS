import re
from typing import List
from urllib.parse import quote

from bs4 import BeautifulSoup

from ..models import AgentLead
from .base import SiteAdapter

PHONE_RE = re.compile(r"(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


class RealtorComAdapter(SiteAdapter):
    """Adapter for realtor.com's public "find an agent" directory.

    IMPORTANT: this environment could not reach realtor.com to confirm its
    current markup (network policy blocked it), so the default selectors
    below are best-effort guesses based on the site's typical structure and
    WILL likely need adjusting. To fix them:

      1. Run the scraper with `headless: false` in config.yaml so a real
         browser window opens.
      2. Right-click an agent card on the page -> Inspect.
      3. Update `selectors.card`, `selectors.name`, `selectors.phone`,
         `selectors.brokerage`, `selectors.profile_link`, and
         `selectors.next_page` in config.yaml to match what you see.

    realtor.com frequently shows a "Show Phone Number" / "Contact Agent"
    button instead of printing the number in the page — if so, `phone` will
    come back empty for that lead and you'll need a different data source
    (or a per-agent profile-page visit, which this adapter does not do by
    default) to get numbers.
    """

    name = "realtor_com"

    DEFAULT_SELECTORS = {
        "card": '[data-testid="agent-card"], .agent-list-card',
        "name": '[data-testid="agent-name"], .agent-name',
        "phone": '[data-testid="agent-phone"], a[href^="tel:"]',
        "brokerage": '[data-testid="agent-group"], .agent-group-name',
        "profile_link": 'a[href]:not([href^="tel:"])',
        "next_page": 'a[aria-label="Go to next page"], a[data-testid="pagination-next"]',
    }

    def __init__(self, city: str, state: str, selectors: dict):
        merged = dict(self.DEFAULT_SELECTORS)
        merged.update(selectors or {})
        super().__init__(city, state, merged)
        self._city_slug = f"{quote(city.strip().lower().replace(' ', '-'))}_{state.strip().lower()}"

    def build_search_url(self, page: int) -> str:
        base = f"https://www.realtor.com/realestateagents/{self._city_slug}"
        if page <= 1:
            return base
        return f"{base}/pg-{page}"

    def parse_listing_page(self, html: str) -> List[AgentLead]:
        soup = BeautifulSoup(html, "lxml")
        leads: List[AgentLead] = []

        cards = soup.select(self.selectors["card"])
        for card in cards:
            name_el = card.select_one(self.selectors["name"])
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name:
                continue

            phone = self._extract_phone(card)

            brokerage_el = card.select_one(self.selectors["brokerage"])
            brokerage = brokerage_el.get_text(strip=True) if brokerage_el else ""

            link_el = card.select_one(self.selectors["profile_link"])
            profile_url = ""
            if link_el and link_el.get("href"):
                href = link_el["href"]
                profile_url = href if href.startswith("http") else f"https://www.realtor.com{href}"

            leads.append(
                AgentLead(
                    name=name,
                    phone=phone,
                    brokerage=brokerage,
                    city=self.city,
                    state=self.state,
                    profile_url=profile_url,
                    source="realtor.com",
                )
            )
        return leads

    def has_next_page(self, html: str) -> bool:
        soup = BeautifulSoup(html, "lxml")
        return soup.select_one(self.selectors["next_page"]) is not None

    def _extract_phone(self, card) -> str:
        phone_el = card.select_one(self.selectors["phone"])
        if phone_el:
            href = phone_el.get("href", "")
            if href.startswith("tel:"):
                return href.replace("tel:", "").strip()
            text = phone_el.get_text(strip=True)
            match = PHONE_RE.search(text)
            if match:
                return match.group(0)

        # Fall back to scanning the whole card's text for a phone-looking
        # string, in case the number isn't behind a dedicated element.
        match = PHONE_RE.search(card.get_text(" ", strip=True))
        return match.group(0) if match else ""
