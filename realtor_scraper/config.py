import os
from dataclasses import dataclass, field
from typing import Optional

import yaml


@dataclass
class Config:
    site: str = "realtor_com"
    city: str = "Las Vegas"
    state: str = "NV"
    max_pages: int = 5
    min_delay: float = 3.0
    max_delay: float = 7.0
    headless: bool = True
    csv_path: str = "output/leads.csv"
    google_sheet_id: Optional[str] = None
    google_credentials_path: Optional[str] = None
    google_worksheet_name: str = "Leads"
    selectors: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: str) -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        known_fields = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in known_fields}
        cfg = cls(**filtered)

        # Allow overriding secrets/paths via environment variables so
        # credentials never need to live in config.yaml.
        cfg.google_sheet_id = os.environ.get("GOOGLE_SHEET_ID", cfg.google_sheet_id)
        cfg.google_credentials_path = os.environ.get(
            "GOOGLE_CREDENTIALS_PATH", cfg.google_credentials_path
        )
        return cfg
