# Las Vegas Realtor Lead Scraper

Pulls realtor name/phone leads for the Las Vegas area and exports them to a
CSV file and/or a Google Sheet, so you can start calling. Two lead sources
are included:

| Source | Risk | Gets phone numbers? | Needs |
|---|---|---|---|
| **Google Places API** (`places_cli.py`) — recommended | Low — official API, not scraping, no ToS conflict | Yes, directly | A free/low-cost Google Maps Platform API key |
| **realtor.com scraper** (`cli.py`) | Higher — realtor.com's ToS prohibits scraping, has anti-bot | Sometimes — often gated behind a "contact agent" click | Nothing but this code |

**Use the Places API path unless you have a specific reason not to.** It's
the lower-risk option you'd expect from an "official business directory"
approach: Google's Places API is built and priced for exactly this kind of
business lookup (name, phone, address), so pulling "real estate agents in
Las Vegas, NV" through it isn't scraping at all — no ToS conflict, no
anti-bot blocking, no brittle CSS selectors to maintain.

## Before you run this

**Legal/compliance, read this first:**

- Cold-calling leads (from either source) is subject to TCPA rules in the
  US. Business lines and B2B calls have more leeway than consumer cell
  numbers, and there's a realtor/B2B carve-out in some National Do Not Call
  Registry cases, but this is not legal advice — check current TCPA/DNC
  rules (or talk to a lawyer) before running a calling campaign at scale.
- If you use the realtor.com scraper instead: its Terms of Service
  prohibit automated scraping. Scraping publicly viewable pages is
  generally not a *criminal* matter, but it is a breach-of-contract risk,
  and the site runs active anti-bot systems that may block you. That
  scraper defaults to slow, randomized delays and doesn't parallelize
  requests, specifically to reduce load on the site — don't remove that
  without a good reason.

**Both were built and tested from a sandbox with no general internet
access** (its network policy blocks browsing to any ordinary website,
realtor.com included — confirmed by testing several other sites, not just
that one). `places.googleapis.com` was the one external host reachable
from that sandbox, so the Places API path was verified end-to-end against
the real live endpoint (confirmed by making an actual request that
returned Google's own "API key not valid" error — i.e. everything up to
supplying a real key works). The realtor.com scraper's parsing logic is
unit-tested against fixture HTML, but its CSS selectors are best-effort
guesses for the live page and will likely need a quick manual tune-up —
see "Fixing selectors" below.

## Quick start: Google Places API (recommended)

1. In [Google Cloud Console](https://console.cloud.google.com/), create/pick
   a project and enable the **"Places API (New)"**.
2. Create an API key (APIs & Services -> Credentials). Billing needs to be
   enabled on the project, but Google's recurring monthly credit covers a
   few thousand searches for this use case in most cases.
3. Run it:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m realtor_scraper.places_cli --api-key YOUR_KEY --max-results 60
# or: export GOOGLE_PLACES_API_KEY=YOUR_KEY and drop --api-key
```

This writes `output/leads_places.csv` (same columns as below). Add
`--sheets --sheet-id ... ` to also push straight to Google Sheets (see
"Google Sheets export" below for credentials setup). Tune the search with
`--query "real estate agents in Henderson, NV"` etc.

## Setup (realtor.com scraper)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

cp config.example.yaml config.yaml
# edit config.yaml: city/state, max_pages, etc.
```

## Run it (CSV only)

```bash
python -m realtor_scraper.cli --config config.yaml
```

This writes leads to `output/leads.csv` (Name, Phone, Brokerage, City,
State, Profile URL, Source, Scraped Date, Called, Notes — the last two are
blank columns for you to fill in while calling).

## Fixing selectors if scraping comes back empty

1. In `config.yaml`, set `headless: false` and re-run. A real Chrome window
   will open on the target page.
2. Right-click an agent listing -> **Inspect**.
3. Find the repeating container element for one agent card, and the
   elements inside it for name/phone/brokerage/profile link.
4. Put the matching CSS selectors under `selectors:` in `config.yaml`, e.g.:
   ```yaml
   selectors:
     card: '[data-testid="agent-card"]'
     name: '[data-testid="agent-name"]'
     phone: 'a[href^="tel:"]'
     brokerage: '[data-testid="agent-group"]'
     profile_link: 'a[href]:not([href^="tel:"])'
     next_page: 'a[aria-label="Go to next page"]'
   ```
5. Re-run with `headless: true`.

If the site shows a "Show phone number" / "Contact agent" button instead of
printing the number in the page, this adapter won't be able to see it (it
doesn't click through to individual contact-reveal flows). In that case
you'll get name/brokerage/profile link with an empty phone column, or you
should point `city`/`state`/`selectors` at a different, more scraper-
friendly directory.

## Google Sheets export

**"Which email do I share the sheet with?"** — there isn't one assigned
ahead of time. This code runs on your own machine (or wherever you run it),
so it authenticates as a **service account** you create yourself in your
own Google Cloud project (steps below) — its email is auto-generated,
something like `leads-writer@your-project.iam.gserviceaccount.com`, and
you'll see it the moment you create it. You share your target sheet with
that address, the same way you'd share it with any collaborator.

(If instead you're working with Claude in a chat session that has a Google
Drive connector enabled, Claude can create/update a Sheet directly in
*your own* connected Google account with no service account needed at all
— that's a different mechanism from this standalone script, which runs
unattended outside any chat session and needs its own credential.)

1. In [Google Cloud Console](https://console.cloud.google.com/), create (or
   pick) a project, then enable the **Google Sheets API** and **Google
   Drive API**.
2. Create a **Service Account** (IAM & Admin -> Service Accounts), then
   create a JSON key for it and download it as `credentials.json` in this
   project's root (it's git-ignored, so it won't get committed).
3. Open your target Google Sheet in a browser, click **Share**, and add the
   service account's email address (looks like
   `something@your-project.iam.gserviceaccount.com`, found inside
   `credentials.json`) as an **Editor**.
4. Copy the Sheet ID from its URL: `https://docs.google.com/spreadsheets/d/`**`THIS_PART`**`/edit`.
5. Put the ID and credentials path in `config.yaml` (or as env vars
   `GOOGLE_SHEET_ID` / `GOOGLE_CREDENTIALS_PATH` if you'd rather not put
   them in the file), then run:

```bash
python -m realtor_scraper.cli --config config.yaml --sheets
```

Leads are appended to a `Leads` worksheet (created automatically if it
doesn't exist). Re-running the scraper skips rows that already exist in the
sheet (matched by phone number, or name+profile URL when no phone was
scraped), so you can re-run it periodically without creating duplicates.

## Pointing this at a different site

The scraper is built around a small adapter interface
(`realtor_scraper/sites/base.py`) so it isn't locked to realtor.com. To
target another directory:

1. Copy `realtor_scraper/sites/realtor_com.py` to a new file.
2. Update `build_search_url`, and the default selectors, for the new site.
3. Register it in `realtor_scraper/sites/__init__.py`'s `ADAPTERS` dict.
4. Set `site: your_new_adapter_name` in `config.yaml`.

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

Tests run against a fixed HTML fixture / mocked API responses, not the
live sites, so they work without network access and verify the parsing
logic itself is correct.
