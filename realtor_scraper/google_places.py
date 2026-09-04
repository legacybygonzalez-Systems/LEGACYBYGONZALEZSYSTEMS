"""Fetch realtor leads via the Google Places API (New) -- Text Search.

This is the recommended lower-risk lead source: it's an official, ToS-
sanctioned API (not scraping), so there's no "against the terms of service"
or anti-bot risk. It returns business name + phone number directly for
real estate agencies/agents matching a text query, e.g. "real estate agents
in Las Vegas, NV".

Confirmed reachable from this environment (places.googleapis.com responds
normally -- it just needs a valid API key, which the caller supplies).

Setup:
  1. In Google Cloud Console, create/select a project and enable the
     "Places API (New)".
  2. Create an API key (APIs & Services -> Credentials). Billing must be
     enabled on the project, but Google gives a recurring monthly credit
     that comfortably covers a few thousand searches for this use case.
  3. Pass the key via --api-key or the GOOGLE_PLACES_API_KEY env var.
"""
import logging
import time
from typing import List, Optional

import requests

from .models import AgentLead

logger = logging.getLogger(__name__)

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join(
    [
        "places.displayName",
        "places.nationalPhoneNumber",
        "places.internationalPhoneNumber",
        "places.formattedAddress",
        "places.googleMapsUri",
        "places.websiteUri",
        "places.id",
        "nextPageToken",
    ]
)


def fetch_leads(
    query: str,
    api_key: str,
    city: str = "",
    state: str = "",
    max_results: int = 60,
    page_delay: float = 2.5,
) -> List[AgentLead]:
    """Run a Places Text Search for `query` (e.g. "real estate agents in Las
    Vegas, NV") and return up to `max_results` leads, following pagination.
    """
    leads: List[AgentLead] = []
    page_token: Optional[str] = None

    while len(leads) < max_results:
        body = {"textQuery": query}
        if page_token:
            body["pageToken"] = page_token

        resp = requests.post(
            SEARCH_URL,
            json=body,
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": FIELD_MASK,
            },
            timeout=15,
        )
        if resp.status_code != 200:
            logger.error("Places API error %s: %s", resp.status_code, resp.text)
            resp.raise_for_status()

        data = resp.json()
        places = data.get("places", [])
        if not places:
            break

        for place in places:
            if len(leads) >= max_results:
                break
            name = place.get("displayName", {}).get("text", "")
            if not name:
                continue
            phone = place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber") or ""
            leads.append(
                AgentLead(
                    name=name,
                    phone=phone,
                    brokerage="",
                    city=city,
                    state=state,
                    profile_url=place.get("googleMapsUri") or place.get("websiteUri") or "",
                    source="Google Places API",
                    notes=place.get("formattedAddress", ""),
                )
            )

        page_token = data.get("nextPageToken")
        if not page_token:
            break
        # A freshly issued page token needs a short delay before it's valid.
        time.sleep(page_delay)

    return leads
