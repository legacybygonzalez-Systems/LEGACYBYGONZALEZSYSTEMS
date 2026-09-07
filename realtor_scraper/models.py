from dataclasses import dataclass, field
from datetime import date


@dataclass
class AgentLead:
    """A single scraped realtor lead."""

    name: str
    phone: str = ""
    website: str = ""
    rating: str = ""
    review_count: str = ""
    business_type: str = ""
    business_status: str = ""
    brokerage: str = ""
    city: str = ""
    state: str = ""
    profile_url: str = ""
    source: str = ""
    scraped_date: str = field(default_factory=lambda: date.today().isoformat())
    called: str = ""
    notes: str = ""

    def dedupe_key(self) -> str:
        # Prefer phone for dedup since two agents can share a display name;
        # fall back to name+profile_url when no phone was exposed on the page.
        if self.phone:
            return self.phone
        return f"{self.name}|{self.profile_url}"

    def as_row(self) -> list:
        return [
            self.name,
            self.phone,
            self.website,
            self.rating,
            self.review_count,
            self.business_type,
            self.business_status,
            self.brokerage,
            self.city,
            self.state,
            self.profile_url,
            self.source,
            self.scraped_date,
            self.called,
            self.notes,
        ]

    @staticmethod
    def header() -> list:
        return [
            "Name",
            "Phone",
            "Website",
            "Rating",
            "Reviews",
            "Type",
            "Status",
            "Brokerage",
            "City",
            "State",
            "Profile URL",
            "Source",
            "Scraped Date",
            "Called",
            "Notes",
        ]
