# Las Vegas Realtor Lead Scraper

Scrapes realtor name/phone leads from a real estate agent directory (default
target: realtor.com's Las Vegas agent search) and exports them to a CSV file
and/or a Google Sheet, so you can start calling.

## Before you run this

**Legal/compliance, read this first:**

- Many large real estate sites (realtor.com, Zillow, etc.) prohibit
  automated scraping in their Terms of Service. Scraping publicly viewable
  pages is generally not a *criminal* matter, but it can be a breach of
  contract, and sites like these run active anti-bot systems that may block
  or rate-limit you. Consider a smaller local directory, a brokerage's own
  public roster, or the Nevada Real Estate Division's public license lookup
  if you want a lower-risk source.
- Cold-calling scraped phone numbers is subject to TCPA rules in the US.
  Business lines and B2B calls have more leeway than consumer cell numbers,
  and the National Do Not Call Registry has a realtor/B2B carve-out in some
  cases, but this is not legal advice — check current TCPA/DNC rules (or
  talk to a lawyer) before running a calling campaign, especially at scale.
- This tool defaults to slow, randomized delays between page loads and does
  not parallelize requests, specifically to avoid hammering the target
  site. Don't remove that without a good reason.

**This code was built without live access to realtor.com** (the sandbox it
was written in couldn't reach the internet). The scraping logic, CSV
export, and Google Sheets export are all tested and working — but the CSS
selectors that find the agent name/phone/brokerage on the actual live page
are best-effort guesses and will very likely need a small tune-up. See
"Fixing selectors" below; it's a 5-minute fix once you can see the real
page.

## Setup

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

Tests run against a fixed HTML fixture, not the live site, so they work
without network access and verify the parsing logic itself is correct.
