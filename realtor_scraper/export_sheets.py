import logging
from typing import List

from .models import AgentLead

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


def push_to_sheet(leads: List[AgentLead], sheet_id: str, credentials_path: str, worksheet_name: str = "Leads") -> int:
    """Append leads to a Google Sheet, skipping rows whose phone (or, if no
    phone, name+profile url) already exists in the sheet. Returns the number
    of new rows written.

    Setup:
      1. Create a Google Cloud project -> enable "Google Sheets API" and
         "Google Drive API".
      2. Create a Service Account -> generate a JSON key -> save it as
         `credentials_path`.
      3. Open your target Google Sheet -> Share -> add the service
         account's email (looks like ...@...iam.gserviceaccount.com) as an
         Editor.
      4. Pass the sheet's ID (the long string in its URL between /d/ and
         /edit) as `sheet_id`.
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError as exc:
        raise RuntimeError(
            "gspread and google-auth are required for Google Sheets export. "
            "Install with `pip install gspread google-auth`."
        ) from exc

    creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_id)

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=len(AgentLead.header()))
        worksheet.append_row(AgentLead.header())

    existing_rows = worksheet.get_all_values()
    if not existing_rows:
        worksheet.append_row(AgentLead.header())
        existing_keys = set()
    else:
        header = existing_rows[0]
        phone_idx = header.index("Phone") if "Phone" in header else 1
        name_idx = header.index("Name") if "Name" in header else 0
        url_idx = header.index("Profile URL") if "Profile URL" in header else 5
        existing_keys = set()
        for row in existing_rows[1:]:
            phone = row[phone_idx] if len(row) > phone_idx else ""
            if phone:
                existing_keys.add(phone)
            else:
                name = row[name_idx] if len(row) > name_idx else ""
                url = row[url_idx] if len(row) > url_idx else ""
                existing_keys.add(f"{name}|{url}")

    new_rows = [lead.as_row() for lead in leads if lead.dedupe_key() not in existing_keys]
    if new_rows:
        worksheet.append_rows(new_rows, value_input_option="RAW")
    logger.info("Wrote %d new rows to sheet (skipped %d duplicates).", len(new_rows), len(leads) - len(new_rows))
    return len(new_rows)
