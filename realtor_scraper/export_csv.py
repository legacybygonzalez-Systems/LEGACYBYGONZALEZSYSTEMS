import csv
import os
from typing import List

from .models import AgentLead


def write_csv(leads: List[AgentLead], path: str) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(AgentLead.header())
        for lead in leads:
            writer.writerow(lead.as_row())
    return path
