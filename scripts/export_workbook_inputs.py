"""Serialize reviewed inputs for Excel authoring. No valuation calculations here."""

import csv
import json
import sys
from pathlib import Path

from shipping_equity.data import load_company

ROOT = Path(__file__).resolve().parents[1]
ticker = sys.argv[1] if len(sys.argv) > 1 else "SBLK"
folder = ROOT / "data/companies" / ticker
payload = {
    name: json.loads((folder / f"{name}.json").read_text())
    for name in ["company", "sources", "assumptions"]
}
payload["input_sha256"] = load_company(folder).fingerprint
for name in ["fleet", "financials", "debt"]:
    with (folder / f"{name}.csv").open() as f:
        payload[name] = list(csv.DictReader(f))
    numeric = {
        "fleet": ["dwt", "build_year", "appraisal_usd", "remaining_capex_usd", "scrubber"],
        "financials": ["value"],
        "debt": ["principal_usd"],
    }[name]
    for row in payload[name]:
        for key in numeric:
            row[key] = float(row[key])
(ROOT / ".cache").mkdir(exist_ok=True)
(ROOT / ".cache/workbook-inputs.json").write_text(json.dumps(payload, indent=2) + "\n")
