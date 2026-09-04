import csv
import os
import tempfile

from realtor_scraper.export_csv import write_csv
from realtor_scraper.models import AgentLead


def test_write_csv_roundtrip():
    leads = [
        AgentLead(name="Jane Smith", phone="7025551234", city="Las Vegas", state="NV"),
        AgentLead(name="John Doe", phone="", city="Las Vegas", state="NV"),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "out", "leads.csv")
        write_csv(leads, path)

        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))

        assert rows[0] == AgentLead.header()
        assert rows[1][0] == "Jane Smith"
        assert rows[1][1] == "7025551234"
        assert rows[2][0] == "John Doe"
