import argparse
import logging
import os
import sys

from .export_csv import write_csv
from .google_places import fetch_leads


def main():
    parser = argparse.ArgumentParser(
        description="Fetch realtor leads via the Google Places API (lower-risk, no scraping)."
    )
    parser.add_argument(
        "--query",
        default="real estate agents in Las Vegas, NV",
        help="Places text search query",
    )
    parser.add_argument("--city", default="Las Vegas")
    parser.add_argument("--state", default="NV")
    parser.add_argument("--max-results", type=int, default=60)
    parser.add_argument(
        "--api-key",
        default=os.environ.get("GOOGLE_PLACES_API_KEY"),
        help="Google Places API key (or set GOOGLE_PLACES_API_KEY env var)",
    )
    parser.add_argument("--csv-path", default="output/leads_places.csv")
    parser.add_argument("--sheets", action="store_true", help="Also push results to Google Sheets")
    parser.add_argument("--sheet-id", default=os.environ.get("GOOGLE_SHEET_ID"))
    parser.add_argument("--credentials-path", default=os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json"))
    parser.add_argument("--worksheet-name", default="Leads")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    log = logging.getLogger("places_cli")

    if not args.api_key:
        log.error("No API key. Pass --api-key or set GOOGLE_PLACES_API_KEY.")
        sys.exit(1)

    log.info("Querying Places API: %r (up to %d results)", args.query, args.max_results)
    leads = fetch_leads(
        query=args.query,
        api_key=args.api_key,
        city=args.city,
        state=args.state,
        max_results=args.max_results,
    )
    log.info("Fetched %d leads.", len(leads))

    csv_path = write_csv(leads, args.csv_path)
    log.info("Wrote CSV: %s", csv_path)

    if args.sheets:
        if not args.sheet_id:
            log.error("--sheets was passed but no --sheet-id / GOOGLE_SHEET_ID set.")
            sys.exit(1)
        from .export_sheets import push_to_sheet

        added = push_to_sheet(
            leads,
            sheet_id=args.sheet_id,
            credentials_path=args.credentials_path,
            worksheet_name=args.worksheet_name,
        )
        log.info("Added %d new rows to Google Sheet.", added)


if __name__ == "__main__":
    main()
