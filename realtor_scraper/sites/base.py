from abc import ABC, abstractmethod
from typing import List

from ..models import AgentLead


class SiteAdapter(ABC):
    """Interface a scraping target implements.

    Selectors and URL patterns are read from the adapter's `selectors` dict
    (populated from config.yaml) rather than hardcoded, so a change on the
    target site's markup only requires editing config, not code.
    """

    name: str = "base"

    def __init__(self, city: str, state: str, selectors: dict):
        self.city = city
        self.state = state
        self.selectors = selectors

    @abstractmethod
    def build_search_url(self, page: int) -> str:
        """Return the URL for a given 1-indexed results page."""

    @abstractmethod
    def parse_listing_page(self, html: str) -> List[AgentLead]:
        """Parse a results page's HTML into a list of leads."""

    @abstractmethod
    def has_next_page(self, html: str) -> bool:
        """Whether a next page of results exists."""
