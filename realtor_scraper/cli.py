import argparse
import logging
import sys

from .config import Config
from .export_csv import write_csv
from .scraper import scrape_leads
from .sites import ADAPTERS


def main():
    parser = argparse.ArgumentParser(description="Scrape realtor leads and export to CSV / Google Sheets.")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--sheets", action="store_true", help="Also push results to Google Sheets")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    log = logging.getLogger("cli")

    cfg = Config.load(args.config)

    adapter_cls = ADAPTERS.get(cfg.site)
    if not adapter_cls:
        log.error("Unknown site adapter '%s'. Available: %s", cfg.site, list(ADAPTERS))
        sys.exit(1)

    adapter = adapter_cls(city=cfg.city, state=cfg.state, selectors=cfg.selectors)

    log.info("Scraping %s, %s from %s (up to %d pages)...", cfg.city, cfg.state, cfg.site, cfg.max_pages)
    leads = scrape_leads(
        adapter,
        max_pages=cfg.max_pages,
        min_delay=cfg.min_delay,
        max_delay=cfg.max_delay,
        headless=cfg.headless,
    )
    log.info("Scraped %d unique leads.", len(leads))

    if not leads:
        log.warning(
            "No leads scraped. This usually means the site's markup changed, "
            "the site blocked the request, or the selectors in config.yaml "
            "need adjusting. Try re-running with headless: false to watch "
            "what the browser actually loads."
        )

    csv_path = write_csv(leads, cfg.csv_path)
    log.info("Wrote CSV: %s", csv_path)

    if args.sheets:
        if not cfg.google_sheet_id or not cfg.google_credentials_path:
            log.error(
                "--sheets was passed but google_sheet_id / google_credentials_path "
                "are not set in config.yaml or via env vars GOOGLE_SHEET_ID / "
                "GOOGLE_CREDENTIALS_PATH."
            )
            sys.exit(1)
        from .export_sheets import push_to_sheet

        added = push_to_sheet(
            leads,
            sheet_id=cfg.google_sheet_id,
            credentials_path=cfg.google_credentials_path,
            worksheet_name=cfg.google_worksheet_name,
        )
        log.info("Added %d new rows to Google Sheet.", added)


if __name__ == "__main__":
    main()
